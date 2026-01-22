"""Audio capture and preprocessing for microphone input."""

from typing import Optional
import numpy as np


class MicrophoneInterface:
    """Interface for capturing audio from microphone."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        """Initialize microphone interface.

        Args:
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels (1 for mono, 2 for stereo)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self._stream = None

    def start(self) -> None:
        """Start the audio stream."""
        raise NotImplementedError("To be implemented")

    def stop(self) -> None:
        """Stop the audio stream."""
        raise NotImplementedError("To be implemented")

    def capture_audio(self, duration: float) -> np.ndarray:
        """Capture audio for specified duration.

        Args:
            duration: Duration in seconds

        Returns:
            Audio data as numpy array
        """
        raise NotImplementedError("To be implemented")

    def get_audio_chunk(self, chunk_size: int) -> np.ndarray:
        """Get a single chunk of audio data.

        Args:
            chunk_size: Number of samples to read

        Returns:
            Audio data as numpy array
        """
        raise NotImplementedError("To be implemented")
