"""Whisper-based speech-to-text transcription."""

from typing import Optional
import numpy as np
import whisper
from ..config import WHISPER_MODEL_SIZE, WHISPER_LANGUAGE


class WhisperTranscriber:
    """Transcribes audio to text using OpenAI Whisper."""

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
        
        self._model = whisper.load_model(self.model_size)
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
        
        # sounddevice provides float32 [-1.0, 1.0], which is exactly what Whisper needs
        if audio_data.dtype == np.int16:
            # Legacy support for int16 (from tests or other sources)
            audio_float = audio_data.astype(np.float32) / 32768.0
        else:
            # Already float32 from sounddevice
            audio_float = audio_data.astype(np.float32)
        
        result = self._model.transcribe(
            audio_float,
            language=language,
            task="transcribe",
            fp16=False  # Use fp32 for CPU compatibility (macOS)
        )
        
        text = result["text"].strip().lower()
        return text

    def transcribe_file(self, audio_path: str) -> str:
        """Transcribe audio from file.

        Args:
            audio_path: Path to audio file

        Returns:
            Transcribed text
        """
        if not self._loaded:
            self.load_model()
        
        result = self._model.transcribe(audio_path, language=WHISPER_LANGUAGE)
        return result["text"].strip().lower()

    def unload_model(self) -> None:
        """Unload model to free memory."""
        self._model = None
        self._loaded = False
