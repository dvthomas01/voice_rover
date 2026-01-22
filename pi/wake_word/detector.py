"""Wake word detection using Porcupine."""

from typing import Callable, Optional
import numpy as np


class WakeWordDetector:
    """Detects wake word in audio stream."""

    def __init__(self, wake_word: str = "jarvis", sensitivity: float = 0.5):
        """Initialize wake word detector.

        Args:
            wake_word: The wake word to detect
            sensitivity: Detection sensitivity (0.0 to 1.0)
        """
        self.wake_word = wake_word
        self.sensitivity = sensitivity
        self._detector = None

    def initialize(self) -> None:
        """Initialize the wake word detection engine."""
        raise NotImplementedError("To be implemented")

    def process_audio(self, audio_chunk: np.ndarray) -> bool:
        """Process audio chunk and check for wake word.

        Args:
            audio_chunk: Audio data as numpy array

        Returns:
            True if wake word detected, False otherwise
        """
        raise NotImplementedError("To be implemented")

    def set_callback(self, callback: Callable[[], None]) -> None:
        """Set callback function to call when wake word is detected.

        Args:
            callback: Function to call on wake word detection
        """
        raise NotImplementedError("To be implemented")

    def cleanup(self) -> None:
        """Clean up resources."""
        raise NotImplementedError("To be implemented")
