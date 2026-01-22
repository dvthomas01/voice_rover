"""Wake word detection using Porcupine.

INTEGRATION POINT: Main controller uses process_audio() in continuous loop
DEPENDENCY: pvporcupine library
WAKE WORD: "jarvis" (configurable in config.py)
"""

from typing import Callable, Optional
import numpy as np
from ..config import WAKE_WORD, WAKE_WORD_SENSITIVITY


class WakeWordDetector:
    """Detects wake word in audio stream."""

    def __init__(self, wake_word: str = None, sensitivity: float = None):
        """Initialize wake word detector.

        Args:
            wake_word: The wake word to detect (defaults to config)
            sensitivity: Detection sensitivity 0.0-1.0 (defaults to config)
        """
        self.wake_word = wake_word or WAKE_WORD
        self.sensitivity = sensitivity or WAKE_WORD_SENSITIVITY
        self._detector = None
        self._callback = None

    def initialize(self) -> None:
        """Initialize the wake word detection engine.
        
        TODO: Initialize Porcupine with wake word
        TODO: Get access key (may need API key from Picovoice)
        TODO: Load wake word model
        """
        # TODO: Initialize Porcupine
        # import pvporcupine
        # 
        # # TODO: Get access key (may need to set as environment variable)
        # access_key = os.getenv('PORCUPINE_ACCESS_KEY', '')
        # 
        # # TODO: Initialize detector
        # self._detector = pvporcupine.create(
        #     access_key=access_key,
        #     keywords=[self.wake_word],
        #     sensitivities=[self.sensitivity]
        # )
        pass

    def process_audio(self, audio_chunk: np.ndarray) -> bool:
        """Process audio chunk and check for wake word.

        Args:
            audio_chunk: Audio data as numpy array (int16 format)

        Returns:
            True if wake word detected, False otherwise
            
        TODO: Process audio through Porcupine
        TODO: Return True if wake word detected
        TODO: Call callback if set
        """
        if self._detector is None:
            return False
        
        # TODO: Process audio
        # keyword_index = self._detector.process(audio_chunk)
        # 
        # if keyword_index >= 0:
        #     if self._callback:
        #         self._callback()
        #     return True
        
        return False

    def set_callback(self, callback: Callable[[], None]) -> None:
        """Set callback function to call when wake word is detected.

        Args:
            callback: Function to call on wake word detection
        """
        self._callback = callback

    def cleanup(self) -> None:
        """Clean up resources.
        
        TODO: Delete Porcupine detector
        """
        # TODO: Cleanup
        # if self._detector:
        #     self._detector.delete()
        #     self._detector = None
        pass
