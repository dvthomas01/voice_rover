"""VOSK-based speech-to-text transcription for Raspberry Pi.

VOSK is optimized for embedded systems and provides:
- Real-time transcription (faster than Whisper)
- Low memory usage (~200-500 MB)
- Offline speech recognition
- Good accuracy for voice commands
- Perfect for Raspberry Pi!

Model download:
    Small model (40 MB): vosk-model-small-en-us-0.15
    https://alphacephei.com/vosk/models
"""

from typing import Optional
import json
import numpy as np
from vosk import Model, KaldiRecognizer
from ..config import VOSK_MODEL_PATH, WHISPER_SAMPLE_RATE


class WhisperTranscriber:
    """Transcribes audio to text using VOSK (lightweight, fast, Pi-optimized).
    
    This class maintains the same interface as WhisperTranscriber for compatibility,
    but uses VOSK for better performance on Raspberry Pi.
    """

    def __init__(self, model_size: str = None):
        """Initialize VOSK transcriber.

        Args:
            model_size: Ignored (for compatibility). VOSK uses model path from config.
        """
        self._model = None
        self._recognizer = None
        self._loaded = False
        self._sample_rate = WHISPER_SAMPLE_RATE  # 16kHz (same as Whisper/Porcupine)

    def load_model(self) -> None:
        """Load the VOSK model into memory."""
        if self._loaded and self._model is not None:
            return
        
        # Load VOSK model from path
        # Model should be downloaded to VOSK_MODEL_PATH (see config.py)
        self._model = Model(VOSK_MODEL_PATH)
        
        # Create recognizer with 16kHz sample rate
        self._recognizer = KaldiRecognizer(self._model, self._sample_rate)
        
        # Configure recognizer for better command recognition
        self._recognizer.SetMaxAlternatives(0)  # We only need the best result
        self._recognizer.SetWords(False)  # We don't need word timing
        
        self._loaded = True

    def transcribe(self, audio_data: np.ndarray, language: str = None) -> str:
        """Transcribe audio to text.

        Args:
            audio_data: Audio data as numpy array (float32 at 16kHz from sounddevice)
            language: Ignored (VOSK model language is fixed at download time)

        Returns:
            Transcribed text (lowercase, trimmed)
        """
        if not self._loaded:
            self.load_model()
        
        if self._recognizer is None:
            return ""
        
        # Convert audio to int16 bytes (VOSK expects this format)
        if audio_data.dtype == np.float32:
            # sounddevice gives float32 [-1.0, 1.0], convert to int16 [-32768, 32767]
            audio_int16 = (audio_data * 32768.0).astype(np.int16)
        else:
            audio_int16 = audio_data.astype(np.int16)
        
        # Convert to bytes
        audio_bytes = audio_int16.tobytes()
        
        # Reset recognizer for new audio
        self._recognizer.Reset()
        
        # Feed audio to recognizer
        # Process in chunks for better compatibility
        chunk_size = 4000  # Process 4000 samples at a time
        for i in range(0, len(audio_bytes), chunk_size * 2):  # *2 because int16 = 2 bytes
            chunk = audio_bytes[i:i + chunk_size * 2]
            self._recognizer.AcceptWaveform(chunk)
        
        # Get final result
        result_json = self._recognizer.FinalResult()
        result = json.loads(result_json)
        
        # Extract text from result
        text = result.get("text", "")
        
        return text.strip().lower()

    def transcribe_file(self, audio_path: str) -> str:
        """Transcribe audio from file.

        Args:
            audio_path: Path to audio file (WAV format, 16kHz recommended)

        Returns:
            Transcribed text
        """
        if not self._loaded:
            self.load_model()
        
        # Read audio file
        import wave
        
        wf = wave.open(audio_path, "rb")
        
        # Verify format
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != self._sample_rate:
            print(f"Warning: Audio file should be mono, 16-bit, {self._sample_rate}Hz")
        
        # Create new recognizer for file
        recognizer = KaldiRecognizer(self._model, wf.getframerate())
        recognizer.SetMaxAlternatives(0)
        recognizer.SetWords(False)
        
        # Process file in chunks
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            recognizer.AcceptWaveform(data)
        
        # Get final result
        result_json = recognizer.FinalResult()
        result = json.loads(result_json)
        text = result.get("text", "")
        
        wf.close()
        
        return text.strip().lower()

    def unload_model(self) -> None:
        """Unload model to free memory."""
        if self._recognizer is not None:
            del self._recognizer
        if self._model is not None:
            del self._model
        self._recognizer = None
        self._model = None
        self._loaded = False
