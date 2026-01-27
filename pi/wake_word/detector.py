"""Wake word detection using Porcupine.

INTEGRATION POINT: Main controller uses process_audio() in continuous loop
DEPENDENCY: pvporcupine library
WAKE WORD: "jarvis" (configurable in config.py)
"""

import logging
import os
from typing import Callable, Optional
import numpy as np
from scipy import signal
from ..config import WAKE_WORD, WAKE_WORD_SENSITIVITY

# Porcupine requires 16kHz audio
PORCUPINE_SAMPLE_RATE = 16000


class WakeWordDetector:
    """Detects wake word in audio stream."""

    def __init__(self, wake_word: str = None, sensitivity: float = None):
        """Initialize wake word detector.

        Args:
            wake_word: The wake word to detect (defaults to config)
            sensitivity: Detection sensitivity 0.0-1.0 (defaults to config)
        """
        self.logger = logging.getLogger(__name__)
        self.wake_word = wake_word or WAKE_WORD
        self.sensitivity = sensitivity or WAKE_WORD_SENSITIVITY
        self._detector = None
        self._callback = None
        self._frame_length = None
        self._resample_buffer = None

    def initialize(self) -> None:
        """Initialize the wake word detection engine.
        
        Gets access key from PORCUPINE_ACCESS_KEY environment variable.
        If access key is missing, logs warning and disables detector (non-fatal).
        """
        try:
            import pvporcupine
        except ImportError:
            self.logger.error("pvporcupine library not installed")
            self._detector = None
            return
        
        access_key = os.getenv('PORCUPINE_ACCESS_KEY', '')
        
        if not access_key:
            self.logger.warning(
                "PORCUPINE_ACCESS_KEY not set. Wake word detection disabled. "
                "Get a free key from https://console.picovoice.ai/"
            )
            self._detector = None
            return
        
        try:
            self._detector = pvporcupine.create(
                access_key=access_key,
                keywords=[self.wake_word],
                sensitivities=[self.sensitivity]
            )
            
            # Get frame length (typically 512 samples at 16kHz)
            self._frame_length = self._detector.frame_length
            self.logger.info(
                f"Wake word detector initialized: '{self.wake_word}' "
                f"(sensitivity={self.sensitivity}, frame_length={self._frame_length})"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Porcupine: {e}")
            self._detector = None

    def process_audio(self, audio_chunk: np.ndarray, sample_rate: int = None) -> bool:
        """Process audio chunk and check for wake word.
        
        Audio must be resampled to 16kHz and sliced into exact frame_length blocks
        before processing. Porcupine is strict about format requirements.

        Args:
            audio_chunk: Audio data as numpy array (int16 format)
            sample_rate: Sample rate of audio_chunk (defaults to 16kHz, assumes already resampled)

        Returns:
            True if wake word detected, False otherwise
        """
        if self._detector is None:
            return False
        
        if self._frame_length is None:
            return False
        
        if len(audio_chunk) == 0:
            return False
        
        try:
            # Resample to 16kHz if needed
            if sample_rate is not None and sample_rate != PORCUPINE_SAMPLE_RATE:
                target_length = int(len(audio_chunk) * PORCUPINE_SAMPLE_RATE / sample_rate)
                if target_length > 0:
                    audio_chunk = signal.resample(audio_chunk, target_length).astype(np.int16)
                else:
                    return False
            
            # Ensure audio is int16 format
            if audio_chunk.dtype != np.int16:
                audio_chunk = audio_chunk.astype(np.int16)
            
            # Check if audio has sufficient amplitude (filter out silence)
            max_amplitude = np.max(np.abs(audio_chunk))
            if max_amplitude < 100:  # Very quiet, likely silence
                return False
            
            # Slice audio into exact frame_length blocks
            # Process each complete frame
            num_frames = len(audio_chunk) // self._frame_length
            
            for i in range(num_frames):
                start_idx = i * self._frame_length
                end_idx = start_idx + self._frame_length
                frame = audio_chunk[start_idx:end_idx]
                
                # Ensure frame is exactly frame_length
                if len(frame) != self._frame_length:
                    continue
                
                # Process frame through Porcupine
                keyword_index = self._detector.process(frame)
                
                if keyword_index >= 0:
                    # Wake word detected (edge-triggered)
                    self.logger.info(f"Wake word '{self.wake_word}' detected")
                    if self._callback:
                        try:
                            self._callback()
                        except Exception as e:
                            self.logger.error(f"Error in wake word callback: {e}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Error processing audio for wake word: {e}")
            return False

    def set_callback(self, callback: Callable[[], None]) -> None:
        """Set callback function to call when wake word is detected.

        Args:
            callback: Function to call on wake word detection (edge-triggered, one call per detection)
        """
        self._callback = callback

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._detector:
            try:
                self._detector.delete()
                self.logger.info("Wake word detector cleaned up")
            except Exception as e:
                self.logger.warning(f"Error cleaning up Porcupine detector: {e}")
            finally:
                self._detector = None
                self._frame_length = None
