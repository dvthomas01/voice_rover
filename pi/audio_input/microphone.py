"""Audio capture and preprocessing for microphone input.

INTEGRATION POINT: Wake word detector uses get_audio_chunk()
INTEGRATION POINT: Whisper transcriber uses capture_audio()
HARDWARE: Samson Go Mic USB (44.1kHz/48kHz, resample to 16kHz for Whisper)
"""

from typing import Optional
import numpy as np
import pyaudio
from ..config import SAMPLE_RATE, AUDIO_CHANNELS, CHUNK_SIZE


class MicrophoneInterface:
    """Interface for capturing audio from microphone."""

    def __init__(self, sample_rate: int = None, channels: int = None):
        """Initialize microphone interface.

        Args:
            sample_rate: Audio sample rate in Hz (defaults to config)
            channels: Number of audio channels (defaults to config)
        """
        self.sample_rate = sample_rate or SAMPLE_RATE
        self.channels = channels or AUDIO_CHANNELS
        self._stream = None
        self._audio = None
        self._running = False

    def start(self) -> None:
        """Start the audio stream.
        
        TODO: Initialize PyAudio
        TODO: Open audio stream with correct format
        TODO: Handle device selection (Samson Go Mic USB)
        TODO: Handle resampling if needed (44.1kHz/48kHz -> 16kHz for Whisper)
        """
        # TODO: Initialize PyAudio
        # self._audio = pyaudio.PyAudio()
        
        # TODO: Open stream
        # self._stream = self._audio.open(
        #     format=pyaudio.paInt16,
        #     channels=self.channels,
        #     rate=self.sample_rate,
        #     input=True,
        #     frames_per_buffer=CHUNK_SIZE
        # )
        
        self._running = True

    def stop(self) -> None:
        """Stop the audio stream.
        
        TODO: Stop and close stream
        TODO: Terminate PyAudio
        """
        self._running = False
        # TODO: Close stream and terminate PyAudio
        # if self._stream:
        #     self._stream.stop_stream()
        #     self._stream.close()
        # if self._audio:
        #     self._audio.terminate()

    def capture_audio(self, duration: float) -> np.ndarray:
        """Capture audio for specified duration.

        Args:
            duration: Duration in seconds

        Returns:
            Audio data as numpy array (int16 format)
            
        TODO: Capture audio for specified duration
        TODO: Convert to numpy array
        TODO: Resample to 16kHz if needed (for Whisper)
        """
        if not self._running:
            raise RuntimeError("Microphone not started")
        
        # TODO: Calculate number of frames needed
        # num_frames = int(self.sample_rate * duration)
        # 
        # # TODO: Read audio data
        # audio_data = []
        # for _ in range(0, num_frames, CHUNK_SIZE):
        #     chunk = self._stream.read(CHUNK_SIZE)
        #     audio_data.append(chunk)
        # 
        # # TODO: Convert to numpy array
        # audio_array = np.frombuffer(b''.join(audio_data), dtype=np.int16)
        # 
        # # TODO: Resample if needed (44.1kHz/48kHz -> 16kHz)
        # if self.sample_rate != 16000:
        #     # Use scipy.signal.resample or similar
        #     pass
        
        # Placeholder
        return np.array([], dtype=np.int16)

    def get_audio_chunk(self, chunk_size: int = None) -> Optional[np.ndarray]:
        """Get a single chunk of audio data.

        Args:
            chunk_size: Number of samples to read (defaults to CHUNK_SIZE)

        Returns:
            Audio data as numpy array, or None if stream not ready
            
        TODO: Read single chunk from stream
        TODO: Convert to numpy array
        """
        if not self._running or not self._stream:
            return None
        
        chunk_size = chunk_size or CHUNK_SIZE
        
        # TODO: Read chunk from stream
        # try:
        #     chunk = self._stream.read(chunk_size, exception_on_overflow=False)
        #     audio_array = np.frombuffer(chunk, dtype=np.int16)
        #     return audio_array
        # except Exception as e:
        #     return None
        
        return None
