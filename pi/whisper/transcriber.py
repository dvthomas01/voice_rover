"""Whisper-based speech-to-text transcription."""

from typing import Optional
import numpy as np


class WhisperTranscriber:
    """Transcribes audio to text using OpenAI Whisper."""

    def __init__(self, model_size: str = "base"):
        """Initialize Whisper transcriber.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self._model = None

    def load_model(self) -> None:
        """Load the Whisper model into memory."""
        raise NotImplementedError("To be implemented")

    def transcribe(self, audio_data: np.ndarray, language: str = "en") -> str:
        """Transcribe audio to text.

        Args:
            audio_data: Audio data as numpy array
            language: Language code (e.g., 'en' for English)

        Returns:
            Transcribed text
        """
        raise NotImplementedError("To be implemented")

    def transcribe_file(self, audio_path: str) -> str:
        """Transcribe audio from file.

        Args:
            audio_path: Path to audio file

        Returns:
            Transcribed text
        """
        raise NotImplementedError("To be implemented")

    def unload_model(self) -> None:
        """Unload model to free memory."""
        raise NotImplementedError("To be implemented")
