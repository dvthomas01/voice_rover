"""Audio capture and preprocessing for microphone input.

INTEGRATION POINT: Wake word detector uses get_audio_chunk()
INTEGRATION POINT: Whisper transcriber uses capture_audio()
HARDWARE: Samson Go Mic USB (44.1kHz/48kHz, resample to 16kHz for Whisper)
"""

import logging
from typing import Optional
import numpy as np
import pyaudio
from scipy import signal
from ..config import SAMPLE_RATE, AUDIO_CHANNELS, CHUNK_SIZE, AUDIO_DEVICE_INDEX

# Whisper requires 16kHz audio
WHISPER_SAMPLE_RATE = 16000


class MicrophoneInterface:
    """Interface for capturing audio from microphone."""

    def __init__(self, sample_rate: int = None, channels: int = None, device_index: int = None):
        """Initialize microphone interface.

        Args:
            sample_rate: Audio sample rate in Hz (defaults to config, or auto-detects device rate)
            channels: Number of audio channels (defaults to config)
            device_index: Optional device index override (defaults to config, then auto-detect)
        """
        self.logger = logging.getLogger(__name__)
        self.channels = channels or AUDIO_CHANNELS
        self.device_index = device_index if device_index is not None else AUDIO_DEVICE_INDEX
        self._stream = None
        self._audio = None
        self._running = False
        self._selected_device_index = None
        
        # Use provided sample rate, or config default, or will auto-detect in start()
        self.sample_rate = sample_rate or SAMPLE_RATE

    def start(self) -> None:
        """Start the audio stream.
        
        Auto-detects device's native sample rate if using default config rate.
        For USB microphones (Samson Go Mic), prefers 44.1kHz.
        For MacBook built-in mic, uses device's native rate (typically 48kHz).
        
        Raises:
            RuntimeError: If no audio device found or stream cannot be opened
        """
        if self._running:
            self.logger.warning("Microphone already started")
            return
        
        try:
            self._audio = pyaudio.PyAudio()
            
            # Find and select audio device
            device_index = self._find_audio_device()
            if device_index is None:
                self._audio.terminate()
                self._audio = None
                raise RuntimeError("No audio input device found")
            
            self._selected_device_index = device_index
            device_info = self._audio.get_device_info_by_index(device_index)
            device_name = device_info['name'].lower()
            
            # Auto-detect sample rate based on device
            # If using config default (44100), check if device prefers different rate
            if self.sample_rate == SAMPLE_RATE:  # Using config default
                device_default_rate = int(device_info['defaultSampleRate'])
                
                # USB microphones (like Samson Go Mic) prefer 44.1kHz
                if 'usb' in device_name or 'samson' in device_name:
                    # Keep 44.1kHz for USB mics
                    self.sample_rate = 44100
                    self.logger.info(f"Using USB microphone sample rate: {self.sample_rate}Hz")
                elif device_default_rate in [44100, 48000]:
                    # Use device's native rate for built-in mics (MacBook, etc.)
                    self.sample_rate = device_default_rate
                    self.logger.info(f"Using device native sample rate: {self.sample_rate}Hz")
                else:
                    # Fallback to config default
                    self.logger.info(f"Using config sample rate: {self.sample_rate}Hz")
            
            self.logger.info(f"Using audio device: {device_info['name']} (index {device_index})")
            
            # Open audio stream
            self._stream = self._audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=CHUNK_SIZE
            )
            
            self._running = True
            self.logger.info(f"Audio stream started at {self.sample_rate}Hz, {self.channels} channel(s)")
            
        except OSError as e:
            self.logger.error(f"Failed to open audio stream: {e}")
            if self._audio:
                self._audio.terminate()
                self._audio = None
            raise RuntimeError(f"Cannot open audio device: {e}") from e

    def stop(self) -> None:
        """Stop the audio stream and cleanup resources."""
        self._running = False
        
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception as e:
                self.logger.warning(f"Error closing audio stream: {e}")
            finally:
                self._stream = None
        
        if self._audio:
            try:
                self._audio.terminate()
            except Exception as e:
                self.logger.warning(f"Error terminating PyAudio: {e}")
            finally:
                self._audio = None
        
        self._selected_device_index = None
        self.logger.info("Audio stream stopped")

    def capture_audio(self, duration: float) -> np.ndarray:
        """Capture audio for specified duration and resample to 16kHz for Whisper.

        Args:
            duration: Duration in seconds

        Returns:
            Audio data as numpy array (int16 format, 16kHz sample rate)
            
        Raises:
            RuntimeError: If microphone not started or stream error occurs
        """
        if not self._running:
            raise RuntimeError("Microphone not started")
        
        if not self._stream:
            raise RuntimeError("Audio stream not available")
        
        if duration <= 0:
            raise ValueError("Duration must be positive")
        
        try:
            # Calculate number of frames needed
            num_frames = int(self.sample_rate * duration)
            
            # Read audio data in chunks
            audio_data = []
            frames_read = 0
            
            while frames_read < num_frames:
                frames_to_read = min(CHUNK_SIZE, num_frames - frames_read)
                chunk = self._stream.read(frames_to_read, exception_on_overflow=False)
                audio_data.append(chunk)
                frames_read += frames_to_read
            
            # Convert bytes to numpy array (int16)
            audio_bytes = b''.join(audio_data)
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # Resample to 16kHz if needed (for Whisper)
            if self.sample_rate != WHISPER_SAMPLE_RATE:
                target_length = int(len(audio_array) * WHISPER_SAMPLE_RATE / self.sample_rate)
                audio_array = signal.resample(audio_array, target_length).astype(np.int16)
                self.logger.debug(f"Resampled audio from {self.sample_rate}Hz to {WHISPER_SAMPLE_RATE}Hz")
            
            return audio_array
            
        except Exception as e:
            self.logger.error(f"Error capturing audio: {e}")
            raise RuntimeError(f"Failed to capture audio: {e}") from e

    def get_audio_chunk(self, chunk_size: int = None) -> Optional[np.ndarray]:
        """Get a single chunk of audio data (blocking read).

        Args:
            chunk_size: Number of samples to read (defaults to CHUNK_SIZE)

        Returns:
            Audio data as numpy array (int16 format), or None if stream not ready
        """
        if not self._running or not self._stream:
            return None
        
        chunk_size = chunk_size or CHUNK_SIZE
        
        try:
            # Blocking read (waits for chunk_size samples)
            chunk = self._stream.read(chunk_size, exception_on_overflow=False)
            audio_array = np.frombuffer(chunk, dtype=np.int16)
            return audio_array
        except Exception as e:
            self.logger.warning(f"Error reading audio chunk: {e}")
            return None

    def _find_audio_device(self) -> Optional[int]:
        """Find appropriate audio input device.
        
        Priority:
        1. Explicitly configured device index
        2. USB microphone (by name match)
        3. Default input device
        
        Returns:
            Device index, or None if no device found
        """
        if self._audio is None:
            return None
        
        # If device index explicitly configured, use it
        if self.device_index is not None:
            try:
                device_info = self._audio.get_device_info_by_index(self.device_index)
                if device_info['maxInputChannels'] > 0:
                    self.logger.info(f"Using configured device index {self.device_index}")
                    return self.device_index
                else:
                    self.logger.warning(f"Configured device index {self.device_index} has no input channels")
            except OSError:
                self.logger.warning(f"Configured device index {self.device_index} not found")
        
        # Search for USB microphone
        usb_device = None
        default_device = None
        
        try:
            default_device = self._audio.get_default_input_device_info()
            default_device_index = default_device['index']
        except OSError:
            default_device = None
            default_device_index = None
        
        device_count = self._audio.get_device_count()
        
        for i in range(device_count):
            try:
                device_info = self._audio.get_device_info_by_index(i)
                
                # Check if device has input channels
                if device_info['maxInputChannels'] == 0:
                    continue
                
                device_name = device_info['name'].lower()
                
                # Prefer USB microphone
                if 'usb' in device_name or 'samson' in device_name:
                    if usb_device is None:
                        usb_device = i
                        self.logger.info(f"Found USB microphone: {device_info['name']} (index {i})")
                
                # Track default device if not already found
                if default_device_index == i:
                    default_device = i
                    
            except OSError:
                continue
        
        # Return USB device if found, otherwise default device
        if usb_device is not None:
            return usb_device
        
        if default_device is not None:
            device_info = self._audio.get_device_info_by_index(default_device)
            self.logger.info(f"Using default input device: {device_info['name']} (index {default_device})")
            return default_device
        
        return None
