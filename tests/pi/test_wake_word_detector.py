"""Unit tests for WakeWordDetector."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import os

from pi.wake_word.detector import WakeWordDetector, PORCUPINE_SAMPLE_RATE


class TestWakeWordDetector:
    """Test cases for WakeWordDetector."""

    def test_init_defaults(self):
        """Test initialization with default parameters."""
        detector = WakeWordDetector()
        assert detector.wake_word == "jarvis"
        assert detector.sensitivity == 0.5
        assert detector._detector is None
        assert detector._callback is None
        assert detector._frame_length is None

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        detector = WakeWordDetector(wake_word="hey_rover", sensitivity=0.8)
        assert detector.wake_word == "hey_rover"
        assert detector.sensitivity == 0.8

    @patch.dict(os.environ, {'PORCUPINE_ACCESS_KEY': 'test_key'})
    @patch('pvporcupine.create')
    def test_initialize_success(self, mock_create):
        """Test successful Porcupine initialization."""
        mock_detector = MagicMock()
        mock_detector.frame_length = 512
        mock_create.return_value = mock_detector
        
        detector = WakeWordDetector()
        detector.initialize()
        
        assert detector._detector == mock_detector
        assert detector._frame_length == 512
        mock_create.assert_called_once_with(
            access_key='test_key',
            keywords=['jarvis'],
            sensitivities=[0.5]
        )

    @patch.dict(os.environ, {}, clear=True)
    def test_initialize_no_access_key(self):
        """Test initialization without access key (non-fatal)."""
        detector = WakeWordDetector()
        detector.initialize()
        
        assert detector._detector is None
        assert detector._frame_length is None

    @patch.dict(os.environ, {'PORCUPINE_ACCESS_KEY': 'test_key'})
    @patch('builtins.__import__')
    def test_initialize_import_error(self, mock_import):
        """Test initialization handles ImportError."""
        def import_side_effect(name, *args, **kwargs):
            if name == 'pvporcupine':
                raise ImportError("Module not found")
            return __import__(name, *args, **kwargs)
        mock_import.side_effect = import_side_effect
        
        detector = WakeWordDetector()
        detector.initialize()
        
        assert detector._detector is None

    @patch.dict(os.environ, {'PORCUPINE_ACCESS_KEY': 'test_key'})
    @patch('pvporcupine.create')
    def test_initialize_creation_error(self, mock_create):
        """Test initialization handles Porcupine creation errors."""
        mock_create.side_effect = Exception("Invalid key")
        
        detector = WakeWordDetector()
        detector.initialize()
        
        assert detector._detector is None

    def test_process_audio_no_detector(self):
        """Test process_audio returns False when detector not initialized."""
        detector = WakeWordDetector()
        audio = np.random.randint(-32768, 32767, size=512, dtype=np.int16)
        
        result = detector.process_audio(audio)
        
        assert result is False

    @patch.dict(os.environ, {'PORCUPINE_ACCESS_KEY': 'test_key'})
    @patch('pvporcupine.create')
    @patch('pi.wake_word.detector.signal.resample')
    def test_process_audio_no_detection(self, mock_resample, mock_create):
        """Test process_audio returns False when no wake word detected."""
        mock_detector = MagicMock()
        mock_detector.frame_length = 512
        mock_detector.process.return_value = -1  # No detection
        mock_create.return_value = mock_detector
        
        detector = WakeWordDetector()
        detector.initialize()
        
        audio = np.random.randint(-32768, 32767, size=512, dtype=np.int16)
        result = detector.process_audio(audio)
        
        assert result is False
        mock_detector.process.assert_called_once()

    @patch.dict(os.environ, {'PORCUPINE_ACCESS_KEY': 'test_key'})
    @patch('pvporcupine.create')
    @patch('pi.wake_word.detector.signal.resample')
    def test_process_audio_detection(self, mock_resample, mock_create):
        """Test process_audio returns True and calls callback when wake word detected."""
        mock_detector = MagicMock()
        mock_detector.frame_length = 512
        mock_detector.process.return_value = 0  # Wake word detected
        mock_create.return_value = mock_detector
        
        callback = Mock()
        
        detector = WakeWordDetector()
        detector.set_callback(callback)
        detector.initialize()
        
        audio = np.random.randint(-32768, 32767, size=512, dtype=np.int16)
        result = detector.process_audio(audio)
        
        assert result is True
        callback.assert_called_once()

    @patch.dict(os.environ, {'PORCUPINE_ACCESS_KEY': 'test_key'})
    @patch('pvporcupine.create')
    @patch('pi.wake_word.detector.signal.resample')
    def test_process_audio_with_resampling(self, mock_resample, mock_create):
        """Test process_audio resamples audio if sample rate differs."""
        mock_detector = MagicMock()
        mock_detector.frame_length = 512
        mock_detector.process.return_value = -1
        
        # Mock resample to return resampled audio
        original_rate = 44100
        resampled_audio = np.random.randint(-32768, 32767, size=512, dtype=np.int16)
        mock_resample.return_value = resampled_audio
        
        mock_create.return_value = mock_detector
        
        detector = WakeWordDetector()
        detector.initialize()
        
        # Audio at 44.1kHz (larger than 512 samples)
        audio_samples = int(512 * original_rate / PORCUPINE_SAMPLE_RATE)
        audio = np.random.randint(-32768, 32767, size=audio_samples, dtype=np.int16)
        
        result = detector.process_audio(audio, sample_rate=original_rate)
        
        assert result is False
        mock_resample.assert_called_once()
        mock_detector.process.assert_called_once()

    @patch.dict(os.environ, {'PORCUPINE_ACCESS_KEY': 'test_key'})
    @patch('pvporcupine.create')
    @patch('pi.wake_word.detector.signal.resample')
    def test_process_audio_multiple_frames(self, mock_resample, mock_create):
        """Test process_audio processes multiple complete frames."""
        mock_detector = MagicMock()
        mock_detector.frame_length = 512
        mock_detector.process.side_effect = [-1, 0]  # No detection, then detection
        
        mock_create.return_value = mock_detector
        
        callback = Mock()
        
        detector = WakeWordDetector()
        detector.set_callback(callback)
        detector.initialize()
        
        # Audio with 2 complete frames
        audio = np.random.randint(-32768, 32767, size=1024, dtype=np.int16)
        result = detector.process_audio(audio)
        
        assert result is True
        assert mock_detector.process.call_count == 2
        callback.assert_called_once()

    @patch.dict(os.environ, {'PORCUPINE_ACCESS_KEY': 'test_key'})
    @patch('pvporcupine.create')
    def test_process_audio_empty_chunk(self, mock_create):
        """Test process_audio handles empty audio chunk."""
        mock_detector = MagicMock()
        mock_detector.frame_length = 512
        mock_create.return_value = mock_detector
        
        detector = WakeWordDetector()
        detector.initialize()
        
        audio = np.array([], dtype=np.int16)
        result = detector.process_audio(audio)
        
        assert result is False
        mock_detector.process.assert_not_called()

    @patch.dict(os.environ, {'PORCUPINE_ACCESS_KEY': 'test_key'})
    @patch('pvporcupine.create')
    @patch('pi.wake_word.detector.signal.resample')
    def test_process_audio_callback_error(self, mock_resample, mock_create):
        """Test process_audio handles callback errors gracefully."""
        mock_detector = MagicMock()
        mock_detector.frame_length = 512
        mock_detector.process.return_value = 0
        mock_create.return_value = mock_detector
        
        callback = Mock(side_effect=Exception("Callback error"))
        
        detector = WakeWordDetector()
        detector.set_callback(callback)
        detector.initialize()
        
        audio = np.random.randint(-32768, 32767, size=512, dtype=np.int16)
        result = detector.process_audio(audio)
        
        # Should still return True despite callback error
        assert result is True
        callback.assert_called_once()

    @patch.dict(os.environ, {'PORCUPINE_ACCESS_KEY': 'test_key'})
    @patch('pvporcupine.create')
    @patch('pi.wake_word.detector.signal.resample')
    def test_process_audio_processing_error(self, mock_resample, mock_create):
        """Test process_audio handles processing errors gracefully."""
        mock_detector = MagicMock()
        mock_detector.frame_length = 512
        mock_detector.process.side_effect = Exception("Processing error")
        mock_create.return_value = mock_detector
        
        detector = WakeWordDetector()
        detector.initialize()
        
        audio = np.random.randint(-32768, 32767, size=512, dtype=np.int16)
        result = detector.process_audio(audio)
        
        assert result is False

    def test_set_callback(self):
        """Test setting callback function."""
        detector = WakeWordDetector()
        callback = Mock()
        
        detector.set_callback(callback)
        
        assert detector._callback == callback

    @patch.dict(os.environ, {'PORCUPINE_ACCESS_KEY': 'test_key'})
    @patch('pvporcupine.create')
    def test_cleanup(self, mock_create):
        """Test cleanup deletes detector."""
        mock_detector = MagicMock()
        mock_detector.frame_length = 512
        mock_create.return_value = mock_detector
        
        detector = WakeWordDetector()
        detector.initialize()
        detector.cleanup()
        
        mock_detector.delete.assert_called_once()
        assert detector._detector is None
        assert detector._frame_length is None

    def test_cleanup_no_detector(self):
        """Test cleanup handles case when detector not initialized."""
        detector = WakeWordDetector()
        detector.cleanup()  # Should not raise

    @patch.dict(os.environ, {'PORCUPINE_ACCESS_KEY': 'test_key'})
    @patch('pvporcupine.create')
    def test_cleanup_delete_error(self, mock_create):
        """Test cleanup handles delete errors gracefully."""
        mock_detector = MagicMock()
        mock_detector.frame_length = 512
        mock_detector.delete.side_effect = Exception("Delete error")
        mock_create.return_value = mock_detector
        
        detector = WakeWordDetector()
        detector.initialize()
        detector.cleanup()  # Should not raise
        
        assert detector._detector is None
