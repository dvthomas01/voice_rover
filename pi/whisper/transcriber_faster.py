"""Faster Whisper-based speech-to-text transcription for Raspberry Pi.

This module uses faster-whisper (CTranslate2 backend) which is:
- 2-4x faster than openai-whisper
- Better ARM compatibility (fewer illegal instruction issues)
- Lower memory usage
- Same accuracy as openai-whisper

Use this on Raspberry Pi for better performance.
"""

from typing import Optional
import numpy as np
from faster_whisper import WhisperModel
from ..config import WHISPER_MODEL_SIZE, WHISPER_LANGUAGE


class WhisperTranscriber:
    """Transcribes audio to text using faster-whisper (optimized for Pi)."""

    def __init__(self, model_size: str = None):
        """Initialize Whisper transcriber.

        Args:
            model_size: Whisper model size (defaults to config)
        """
        self.model_size = model_size or WHISPER_MODEL_SIZE
        self._model = None
        self._loaded = False

    def load_model(self) -> None:
        """Load the Whisper model into memory."""
        if self._loaded and self._model is not None:
            return
        
        # Load faster-whisper model with ARM-optimized settings
        # - device="cpu": Use CPU (no CUDA on Pi)
        # - compute_type="int8": Quantization for speed and lower memory
        # - cpu_threads: Use all available cores
        self._model = WhisperModel(
            self.model_size,
            device="cpu",
            compute_type="int8",  # Quantization: int8 for speed, float32 for accuracy
            num_workers=1  # Single worker to avoid threading issues on Pi
        )
        self._loaded = True

    def transcribe(self, audio_data: np.ndarray, language: str = None) -> str:
        """Transcribe audio to text.

        Args:
            audio_data: Audio data as numpy array (float32 at 16kHz from sounddevice)
            language: Language code (defaults to config)

        Returns:
            Transcribed text (lowercase, trimmed)
        """
        if not self._loaded:
            self.load_model()
        
        if self._model is None:
            return ""
        
        language = language or WHISPER_LANGUAGE
        
        # faster-whisper expects float32 [-1.0, 1.0] audio at 16kHz (same as openai-whisper)
        if audio_data.dtype == np.int16:
            # Convert int16 to float32
            audio_float = audio_data.astype(np.float32) / 32768.0
        else:
            # Already float32 from sounddevice
            audio_float = audio_data.astype(np.float32)
        
        # Transcribe with faster-whisper
        # Returns iterator of segments
        segments, info = self._model.transcribe(
            audio_float,
            language=language,
            task="transcribe",
            beam_size=1,  # Use beam_size=1 for speed (greedy decoding), 5 for accuracy
            vad_filter=False,  # Disable VAD for simplicity (we already have wake word)
            without_timestamps=True  # We don't need timestamps for commands
        )
        
        # Collect all segment text
        text = " ".join(segment.text for segment in segments)
        return text.strip().lower()

    def transcribe_file(self, audio_path: str) -> str:
        """Transcribe audio from file.

        Args:
            audio_path: Path to audio file

        Returns:
            Transcribed text
        """
        if not self._loaded:
            self.load_model()
        
        segments, info = self._model.transcribe(
            audio_path,
            language=WHISPER_LANGUAGE,
            beam_size=1,
            without_timestamps=True
        )
        
        text = " ".join(segment.text for segment in segments)
        return text.strip().lower()

    def unload_model(self) -> None:
        """Unload model to free memory."""
        if self._model is not None:
            # faster-whisper cleanup
            del self._model
        self._model = None
        self._loaded = False
