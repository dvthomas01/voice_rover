"""Audio capture and preprocessing for microphone input.

INTEGRATION POINT: Wake word detector uses get_audio_chunk()
INTEGRATION POINT: Whisper transcriber uses capture_audio()
HARDWARE: Works with USB microphones (Samson Go Mic) and built-in mics
IMPLEMENTATION: Uses sounddevice for reliable cross-platform audio capture
"""

import logging
import queue
import threading
from typing import Optional
import numpy as np
import sounddevice as sd
from ..config import AUDIO_CHANNELS, CHUNK_SIZE, AUDIO_DEVICE_INDEX

# Whisper and Porcupine require 16kHz audio
WHISPER_SAMPLE_RATE = 16000


class MicrophoneInterface:
    """Interface for capturing audio from microphone using sounddevice."""

    def __init__(self, sample_rate: int = None, channels: int = None, device_index: int = None):
        """Initialize microphone interface.

        Args:
            sample_rate: Audio sample rate in Hz (defaults to 16kHz for Whisper/Porcupine)
            channels: Number of audio channels (defaults to config)
            device_index: Optional device index override (defaults to config, then auto-detect)
        """
        self.logger = logging.getLogger(__name__)
        self.channels = channels or AUDIO_CHANNELS
        self.device_index = device_index if device_index is not None else AUDIO_DEVICE_INDEX
        self.sample_rate = sample_rate or WHISPER_SAMPLE_RATE  # Default to 16kHz
        
        self._stream = None
        self._running = False
        self._selected_device_index = None
        
        # Audio queue for callback-based streaming
        self._audio_queue = queue.Queue()
        self._chunk_event = threading.Event()

    def start(self) -> None:
        """Start the audio stream.
        
        Uses sounddevice for reliable cross-platform audio capture.
        Captures audio directly at 16kHz float32 (Whisper-ready format).
        
        Raises:
            RuntimeError: If no audio device found or stream cannot be opened
        """
        if self._running:
            self.logger.warning("Microphone already started")
            return
        
        try:
            # Find and select audio device
            device_index = self._find_audio_device()
            if device_index is None:
                raise RuntimeError("No audio input device found")
            
            self._selected_device_index = device_index
            device_info = sd.query_devices(device_index)
            
            self.logger.info(f"Using audio device: {device_info['name']} (index {device_index})")
            
            # Audio callback for streaming
            def audio_callback(indata, frames, time_info, status):
                """Callback invoked by sounddevice for each audio block."""
                if status:
                    self.logger.warning(f"Audio stream status: {status}")
                
                # Copy audio data to queue (flatten to 1D if multi-channel)
                audio_chunk = indata.copy().flatten() if indata.ndim > 1 else indata.copy()
                self._audio_queue.put(audio_chunk)
                self._chunk_event.set()
            
            # Open audio stream with sounddevice
            # - 16kHz sample rate (Whisper and Porcupine compatible)
            # - float32 dtype (Whisper-ready, range -1.0 to 1.0)
            # - Callback-based for continuous streaming
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32,
                device=device_index,
                blocksize=CHUNK_SIZE,
                callback=audio_callback
            )
            
            self._stream.start()
            self._running = True
            
            self.logger.info(f"Audio stream started at {self.sample_rate}Hz, {self.channels} channel(s), float32")
            
        except Exception as e:
            self.logger.error(f"Failed to open audio stream: {e}")
            if self._stream:
                try:
                    self._stream.close()
                except:
                    pass
                self._stream = None
            raise RuntimeError(f"Cannot open audio device: {e}") from e

    def stop(self) -> None:
        """Stop the audio stream and cleanup resources."""
        self._running = False
        
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                self.logger.warning(f"Error closing audio stream: {e}")
            finally:
                self._stream = None
        
        # Clear audio queue
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break
        
        self._chunk_event.clear()
        self._selected_device_index = None
        self.logger.info("Audio stream stopped")

    def capture_audio(self, duration: float) -> np.ndarray:
        """Capture audio for specified duration (already at 16kHz float32 for Whisper).

        Args:
            duration: Duration in seconds

        Returns:
            Audio data as numpy array (float32 format, 16kHz sample rate)
            
        Raises:
            RuntimeError: If microphone not started or stream error occurs
        """
        if not self._running:
            raise RuntimeError("Microphone not started")
        
        if duration <= 0:
            raise ValueError("Duration must be positive")
        
        try:
            # Calculate number of samples needed
            num_samples = int(self.sample_rate * duration)
            
            # Collect audio blocks until we have enough samples
            audio_blocks = []
            samples_collected = 0
            
            while samples_collected < num_samples:
                try:
                    # Get audio block from queue (with timeout)
                    block = self._audio_queue.get(timeout=duration + 1.0)
                    audio_blocks.append(block)
                    samples_collected += len(block)
                except queue.Empty:
                    self.logger.warning(f"Timeout while capturing audio (got {samples_collected}/{num_samples} samples)")
                    break
            
            if not audio_blocks:
                self.logger.warning("No audio captured")
                return np.array([], dtype=np.float32)
            
            # Concatenate and trim to exact duration
            audio_array = np.concatenate(audio_blocks)
            audio_array = audio_array[:num_samples]
            
            self.logger.debug(f"Captured {len(audio_array)} samples ({len(audio_array)/self.sample_rate:.2f}s) at {self.sample_rate}Hz")
            
            return audio_array
            
        except Exception as e:
            self.logger.error(f"Error capturing audio: {e}")
            raise RuntimeError(f"Failed to capture audio: {e}") from e

    def get_audio_chunk(self, chunk_size: int = None) -> Optional[np.ndarray]:
        """Get a single chunk of audio data (non-blocking).

        Args:
            chunk_size: Number of samples to read (defaults to CHUNK_SIZE)

        Returns:
            Audio data as numpy array (float32 format), or None if no data available
        """
        if not self._running:
            return None
        
        chunk_size = chunk_size or CHUNK_SIZE
        
        try:
            # Non-blocking get from queue
            audio_chunk = self._audio_queue.get_nowait()
            
            # Trim or pad to requested chunk size if needed
            if len(audio_chunk) > chunk_size:
                return audio_chunk[:chunk_size]
            elif len(audio_chunk) < chunk_size:
                # Pad with zeros if chunk is smaller than requested
                padded = np.zeros(chunk_size, dtype=np.float32)
                padded[:len(audio_chunk)] = audio_chunk
                return padded
            else:
                return audio_chunk
                
        except queue.Empty:
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
        # If device index explicitly configured, use it
        if self.device_index is not None:
            try:
                device_info = sd.query_devices(self.device_index)
                if device_info['max_input_channels'] > 0:
                    self.logger.info(f"Using configured device index {self.device_index}")
                    return self.device_index
                else:
                    self.logger.warning(f"Configured device index {self.device_index} has no input channels")
            except (ValueError, sd.PortAudioError):
                self.logger.warning(f"Configured device index {self.device_index} not found")
        
        # Search for USB microphone or default device
        usb_device = None
        default_device = None
        
        try:
            devices = sd.query_devices()
            default_input = sd.default.device[0]  # (input_device, output_device)
            
            for i, device in enumerate(devices):
                # Skip output-only devices
                if device['max_input_channels'] == 0:
                    continue
                
                device_name = device['name'].lower()
                
                # Prefer USB microphone (Samson Go Mic, etc.)
                if 'usb' in device_name or 'samson' in device_name:
                    if usb_device is None:
                        usb_device = i
                        self.logger.info(f"Found USB microphone: {device['name']} (index {i})")
                
                # Track default input device
                if i == default_input:
                    default_device = i
            
            # Return USB device if found, otherwise default device
            if usb_device is not None:
                return usb_device
            
            if default_device is not None:
                device_info = sd.query_devices(default_device)
                self.logger.info(f"Using default input device: {device_info['name']} (index {default_device})")
                return default_device
            
        except Exception as e:
            self.logger.error(f"Error querying audio devices: {e}")
        
        return None
