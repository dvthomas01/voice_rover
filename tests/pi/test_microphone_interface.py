"""Unit tests for MicrophoneInterface."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import pyaudio

from pi.audio_input.microphone import MicrophoneInterface, WHISPER_SAMPLE_RATE


class TestMicrophoneInterface:
    """Test cases for MicrophoneInterface."""

    def test_init_defaults(self):
        """Test initialization with default parameters."""
        mic = MicrophoneInterface()
        assert mic.sample_rate == 44100
        assert mic.channels == 1
        assert mic.device_index is None
        assert mic._stream is None
        assert mic._audio is None
        assert not mic._running

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        mic = MicrophoneInterface(sample_rate=48000, channels=2, device_index=5)
        assert mic.sample_rate == 48000
        assert mic.channels == 2
        assert mic.device_index == 5

    @patch('pi.audio_input.microphone.pyaudio.PyAudio')
    def test_start_success(self, mock_pyaudio_class):
        """Test successful audio stream start."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_pyaudio_class.return_value = mock_audio
        
        # Mock device info
        mock_device_info = {
            'name': 'USB Microphone',
            'maxInputChannels': 1,
            'index': 0
        }
        mock_audio.get_device_info_by_index.return_value = mock_device_info
        mock_audio.get_device_count.return_value = 1
        mock_audio.get_default_input_device_info.return_value = mock_device_info
        mock_audio.open.return_value = mock_stream
        
        mic = MicrophoneInterface()
        mic.start()
        
        assert mic._running
        assert mic._audio == mock_audio
        assert mic._stream == mock_stream
        mock_audio.open.assert_called_once()

    @patch('pi.audio_input.microphone.pyaudio.PyAudio')
    def test_start_no_device_found(self, mock_pyaudio_class):
        """Test start fails when no audio device found."""
        mock_audio = MagicMock()
        mock_pyaudio_class.return_value = mock_audio
        mock_audio.get_device_count.return_value = 0
        
        # Mock get_default_input_device_info to raise OSError
        mock_audio.get_default_input_device_info.side_effect = OSError("No device")
        
        mic = MicrophoneInterface()
        
        with pytest.raises(RuntimeError, match="No audio input device found"):
            mic.start()
        
        assert not mic._running
        mock_audio.terminate.assert_called_once()

    @patch('pi.audio_input.microphone.pyaudio.PyAudio')
    def test_start_os_error(self, mock_pyaudio_class):
        """Test start handles OSError during stream opening."""
        mock_audio = MagicMock()
        mock_pyaudio_class.return_value = mock_audio
        
        mock_device_info = {
            'name': 'USB Microphone',
            'maxInputChannels': 1,
            'index': 0
        }
        mock_audio.get_device_info_by_index.return_value = mock_device_info
        mock_audio.get_device_count.return_value = 1
        mock_audio.get_default_input_device_info.return_value = mock_device_info
        mock_audio.open.side_effect = OSError("Device busy")
        
        mic = MicrophoneInterface()
        
        with pytest.raises(RuntimeError, match="Cannot open audio device"):
            mic.start()
        
        mock_audio.terminate.assert_called_once()

    def test_stop_not_started(self):
        """Test stop when not started."""
        mic = MicrophoneInterface()
        mic.stop()  # Should not raise
        
        assert not mic._running

    @patch('pi.audio_input.microphone.pyaudio.PyAudio')
    def test_stop_cleanup(self, mock_pyaudio_class):
        """Test stop cleans up resources."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_pyaudio_class.return_value = mock_audio
        
        mock_device_info = {
            'name': 'USB Microphone',
            'maxInputChannels': 1,
            'index': 0
        }
        mock_audio.get_device_info_by_index.return_value = mock_device_info
        mock_audio.get_device_count.return_value = 1
        mock_audio.get_default_input_device_info.return_value = mock_device_info
        mock_audio.open.return_value = mock_stream
        
        mic = MicrophoneInterface()
        mic.start()
        mic.stop()
        
        mock_stream.stop_stream.assert_called_once()
        mock_stream.close.assert_called_once()
        mock_audio.terminate.assert_called_once()
        assert not mic._running
        assert mic._stream is None
        assert mic._audio is None

    @patch('pi.audio_input.microphone.pyaudio.PyAudio')
    def test_stop_handles_errors(self, mock_pyaudio_class):
        """Test stop handles errors during cleanup."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_pyaudio_class.return_value = mock_audio
        
        mock_device_info = {
            'name': 'USB Microphone',
            'maxInputChannels': 1,
            'index': 0
        }
        mock_audio.get_device_info_by_index.return_value = mock_device_info
        mock_audio.get_device_count.return_value = 1
        mock_audio.get_default_input_device_info.return_value = mock_device_info
        mock_audio.open.return_value = mock_stream
        mock_stream.close.side_effect = Exception("Close error")
        
        mic = MicrophoneInterface()
        mic.start()
        mic.stop()  # Should not raise
        
        assert not mic._running

    @patch('pi.audio_input.microphone.pyaudio.PyAudio')
    def test_get_audio_chunk_not_started(self, mock_pyaudio_class):
        """Test get_audio_chunk returns None when not started."""
        mic = MicrophoneInterface()
        assert mic.get_audio_chunk() is None

    @patch('pi.audio_input.microphone.pyaudio.PyAudio')
    def test_get_audio_chunk_success(self, mock_pyaudio_class):
        """Test get_audio_chunk reads audio data."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_pyaudio_class.return_value = mock_audio
        
        # Create mock audio data (1024 samples = 2048 bytes for int16)
        mock_audio_data = np.random.randint(-32768, 32767, size=1024, dtype=np.int16)
        mock_stream.read.return_value = mock_audio_data.tobytes()
        
        mock_device_info = {
            'name': 'USB Microphone',
            'maxInputChannels': 1,
            'index': 0
        }
        mock_audio.get_device_info_by_index.return_value = mock_device_info
        mock_audio.get_device_count.return_value = 1
        mock_audio.get_default_input_device_info.return_value = mock_device_info
        mock_audio.open.return_value = mock_stream
        
        mic = MicrophoneInterface()
        mic.start()
        
        chunk = mic.get_audio_chunk()
        
        assert chunk is not None
        assert isinstance(chunk, np.ndarray)
        assert chunk.dtype == np.int16
        assert len(chunk) == 1024
        mock_stream.read.assert_called_once()

    @patch('pi.audio_input.microphone.pyaudio.PyAudio')
    def test_get_audio_chunk_read_error(self, mock_pyaudio_class):
        """Test get_audio_chunk handles read errors."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_pyaudio_class.return_value = mock_audio
        mock_stream.read.side_effect = Exception("Read error")
        
        mock_device_info = {
            'name': 'USB Microphone',
            'maxInputChannels': 1,
            'index': 0
        }
        mock_audio.get_device_info_by_index.return_value = mock_device_info
        mock_audio.get_device_count.return_value = 1
        mock_audio.get_default_input_device_info.return_value = mock_device_info
        mock_audio.open.return_value = mock_stream
        
        mic = MicrophoneInterface()
        mic.start()
        
        chunk = mic.get_audio_chunk()
        
        assert chunk is None

    @patch('pi.audio_input.microphone.pyaudio.PyAudio')
    @patch('pi.audio_input.microphone.signal.resample')
    def test_capture_audio_not_started(self, mock_resample, mock_pyaudio_class):
        """Test capture_audio raises when not started."""
        mic = MicrophoneInterface()
        
        with pytest.raises(RuntimeError, match="Microphone not started"):
            mic.capture_audio(1.0)

    @patch('pi.audio_input.microphone.pyaudio.PyAudio')
    @patch('pi.audio_input.microphone.signal.resample')
    def test_capture_audio_success_no_resample(self, mock_resample, mock_pyaudio_class):
        """Test capture_audio captures audio without resampling (already 16kHz)."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_pyaudio_class.return_value = mock_audio
        
        # Create mock audio data
        duration = 1.0
        sample_rate = 16000  # Already at Whisper rate
        num_samples = int(sample_rate * duration)
        mock_audio_data = np.random.randint(-32768, 32767, size=num_samples, dtype=np.int16)
        
        # Mock stream.read to return chunks
        chunk_size = 1024
        chunks = []
        for i in range(0, num_samples, chunk_size):
            chunk = mock_audio_data[i:i+chunk_size]
            chunks.append(chunk.tobytes())
        mock_stream.read.side_effect = chunks
        
        mock_device_info = {
            'name': 'USB Microphone',
            'maxInputChannels': 1,
            'index': 0
        }
        mock_audio.get_device_info_by_index.return_value = mock_device_info
        mock_audio.get_device_count.return_value = 1
        mock_audio.get_default_input_device_info.return_value = mock_device_info
        mock_audio.open.return_value = mock_stream
        
        mic = MicrophoneInterface(sample_rate=16000)
        mic.start()
        
        audio = mic.capture_audio(duration)
        
        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.int16
        assert len(audio) == num_samples
        mock_resample.assert_not_called()

    @patch('pi.audio_input.microphone.pyaudio.PyAudio')
    @patch('pi.audio_input.microphone.signal.resample')
    def test_capture_audio_with_resample(self, mock_resample, mock_pyaudio_class):
        """Test capture_audio resamples from 44.1kHz to 16kHz."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_pyaudio_class.return_value = mock_audio
        
        duration = 1.0
        sample_rate = 44100
        num_samples = int(sample_rate * duration)
        target_samples = int(WHISPER_SAMPLE_RATE * duration)
        
        mock_audio_data = np.random.randint(-32768, 32767, size=num_samples, dtype=np.int16)
        
        # Mock resample to return resampled data
        resampled_data = np.random.randint(-32768, 32767, size=target_samples, dtype=np.int16)
        mock_resample.return_value = resampled_data
        
        # Mock stream.read to return chunks
        chunk_size = 1024
        chunks = []
        for i in range(0, num_samples, chunk_size):
            chunk = mock_audio_data[i:i+chunk_size]
            chunks.append(chunk.tobytes())
        mock_stream.read.side_effect = chunks
        
        mock_device_info = {
            'name': 'USB Microphone',
            'maxInputChannels': 1,
            'index': 0
        }
        mock_audio.get_device_info_by_index.return_value = mock_device_info
        mock_audio.get_device_count.return_value = 1
        mock_audio.get_default_input_device_info.return_value = mock_device_info
        mock_audio.open.return_value = mock_stream
        
        mic = MicrophoneInterface(sample_rate=sample_rate)
        mic.start()
        
        audio = mic.capture_audio(duration)
        
        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.int16
        assert len(audio) == target_samples
        mock_resample.assert_called_once()

    @patch('pi.audio_input.microphone.pyaudio.PyAudio')
    def test_capture_audio_invalid_duration(self, mock_pyaudio_class):
        """Test capture_audio validates duration."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_pyaudio_class.return_value = mock_audio
        
        mock_device_info = {
            'name': 'USB Microphone',
            'maxInputChannels': 1,
            'index': 0
        }
        mock_audio.get_device_info_by_index.return_value = mock_device_info
        mock_audio.get_device_count.return_value = 1
        mock_audio.get_default_input_device_info.return_value = mock_device_info
        mock_audio.open.return_value = mock_stream
        
        mic = MicrophoneInterface()
        mic.start()
        
        with pytest.raises(ValueError, match="Duration must be positive"):
            mic.capture_audio(0)

    @patch('pi.audio_input.microphone.pyaudio.PyAudio')
    def test_capture_audio_stream_error(self, mock_pyaudio_class):
        """Test capture_audio handles stream errors."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_pyaudio_class.return_value = mock_audio
        mock_stream.read.side_effect = Exception("Stream error")
        
        mock_device_info = {
            'name': 'USB Microphone',
            'maxInputChannels': 1,
            'index': 0
        }
        mock_audio.get_device_info_by_index.return_value = mock_device_info
        mock_audio.get_device_count.return_value = 1
        mock_audio.get_default_input_device_info.return_value = mock_device_info
        mock_audio.open.return_value = mock_stream
        
        mic = MicrophoneInterface()
        mic.start()
        
        with pytest.raises(RuntimeError, match="Failed to capture audio"):
            mic.capture_audio(1.0)

    @patch('pi.audio_input.microphone.pyaudio.PyAudio')
    def test_find_audio_device_usb_preferred(self, mock_pyaudio_class):
        """Test device selection prefers USB microphone."""
        mock_audio = MagicMock()
        mock_pyaudio_class.return_value = mock_audio
        
        mock_audio.get_device_count.return_value = 3
        
        # USB device
        usb_device = {
            'name': 'USB Microphone',
            'maxInputChannels': 1,
            'index': 0
        }
        
        # Non-USB device
        default_device = {
            'name': 'Built-in Microphone',
            'maxInputChannels': 1,
            'index': 1
        }
        
        # Device with no input channels
        no_input_device = {
            'name': 'Output Only',
            'maxInputChannels': 0,
            'index': 2
        }
        
        def get_device_info_side_effect(index):
            devices = {
                0: usb_device,
                1: default_device,
                2: no_input_device
            }
            return devices.get(index, {'name': 'Unknown', 'maxInputChannels': 0, 'index': index})
        
        mock_audio.get_device_info_by_index.side_effect = get_device_info_side_effect
        mock_audio.get_default_input_device_info.return_value = default_device
        
        mic = MicrophoneInterface()
        mic._audio = mock_audio
        
        device_index = mic._find_audio_device()
        
        assert device_index == 0  # USB device selected

    @patch('pi.audio_input.microphone.pyaudio.PyAudio')
    def test_find_audio_device_fallback_to_default(self, mock_pyaudio_class):
        """Test device selection falls back to default if no USB."""
        mock_audio = MagicMock()
        mock_pyaudio_class.return_value = mock_audio
        
        mock_audio.get_device_count.return_value = 1
        
        default_device = {
            'name': 'Built-in Microphone',
            'maxInputChannels': 1,
            'index': 0
        }
        
        mock_audio.get_device_info_by_index.return_value = default_device
        mock_audio.get_default_input_device_info.return_value = default_device
        
        mic = MicrophoneInterface()
        mic._audio = mock_audio
        
        device_index = mic._find_audio_device()
        
        assert device_index == 0  # Default device selected

    @patch('pi.audio_input.microphone.pyaudio.PyAudio')
    def test_find_audio_device_configured_index(self, mock_pyaudio_class):
        """Test device selection uses configured index if set."""
        mock_audio = MagicMock()
        mock_pyaudio_class.return_value = mock_audio
        
        configured_device = {
            'name': 'Configured Device',
            'maxInputChannels': 1,
            'index': 5
        }
        
        mock_audio.get_device_info_by_index.return_value = configured_device
        
        mic = MicrophoneInterface(device_index=5)
        mic._audio = mock_audio
        
        device_index = mic._find_audio_device()
        
        assert device_index == 5
