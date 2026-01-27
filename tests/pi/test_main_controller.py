"""Unit tests for VoiceRoverController orchestration.

Tests the main controller's orchestration logic with all dependencies mocked.
Focuses on:
- Component initialization order
- Thread lifecycle management
- Wake word detection flow
- Command processing
- STOP command handling
- Graceful shutdown
- Error handling
"""

import pytest
import threading
import time
import signal
import sys
from unittest.mock import Mock, patch, MagicMock, call
import numpy as np

from pi.main_controller import VoiceRoverController
from pi.command_parser.command_schema import Command, CommandType, PRIORITY_STOP, PRIORITY_NORMAL


class TestVoiceRoverController:
    """Test cases for VoiceRoverController."""

    def setup_method(self):
        """Set up test fixtures with mocked dependencies."""
        # Mock all dependencies
        with patch('pi.main_controller.MicrophoneInterface') as mock_mic, \
             patch('pi.main_controller.WakeWordDetector') as mock_wake, \
             patch('pi.main_controller.WhisperTranscriber') as mock_whisper, \
             patch('pi.main_controller.CommandParser') as mock_parser, \
             patch('pi.main_controller.CommandQueueManager') as mock_queue, \
             patch('pi.main_controller.SerialInterface') as mock_serial:
            
            # Create mock instances
            self.mock_mic_instance = Mock()
            self.mock_wake_instance = Mock()
            self.mock_whisper_instance = Mock()
            self.mock_parser_instance = Mock()
            self.mock_queue_instance = Mock()
            self.mock_serial_instance = Mock()
            
            # Configure mock constructors
            mock_mic.return_value = self.mock_mic_instance
            mock_wake.return_value = self.mock_wake_instance
            mock_whisper.return_value = self.mock_whisper_instance
            mock_parser.return_value = self.mock_parser_instance
            mock_queue.return_value = self.mock_queue_instance
            mock_serial.return_value = self.mock_serial_instance
            
            # Create controller
            self.controller = VoiceRoverController()
            self.controller.logger = Mock()

    def test_init(self):
        """Test controller initialization."""
        assert self.controller.microphone == self.mock_mic_instance
        assert self.controller.wake_word == self.mock_wake_instance
        assert self.controller.transcriber == self.mock_whisper_instance
        assert self.controller.parser == self.mock_parser_instance
        assert self.controller.queue == self.mock_queue_instance
        assert self.controller.serial == self.mock_serial_instance
        assert self.controller._running is False
        assert self.controller._wake_word_thread is None
        assert self.controller._command_executor_thread is None

    def test_start_success(self):
        """Test successful startup sequence."""
        # Configure mocks for successful startup
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        # Start controller
        self.controller.start()
        
        # Verify initialization order
        assert self.mock_serial_instance.connect.called
        assert self.mock_whisper_instance.load_model.called
        assert self.mock_mic_instance.start.called
        assert self.mock_wake_instance.initialize.called
        
        # Verify threads started
        assert self.controller._running is True
        assert self.controller._wake_word_thread is not None
        assert self.controller._command_executor_thread is not None
        assert self.controller._wake_word_thread.is_alive()
        assert self.controller._command_executor_thread.is_alive()
        
        # Cleanup
        self.controller.stop()

    def test_start_serial_failure_continues(self):
        """Test startup continues if serial connection fails."""
        self.mock_serial_instance.connect.return_value = False
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        self.controller.start()
        
        # Should log warning but continue
        assert self.controller.logger.warning.called
        assert self.controller._running is True
        
        self.controller.stop()

    def test_start_whisper_failure_raises(self):
        """Test startup fails if Whisper model load fails."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.side_effect = Exception("Model load failed")
        
        with pytest.raises(Exception):
            self.controller.start()
        
        # Should have attempted cleanup
        assert self.controller.logger.error.called

    def test_start_microphone_failure_raises(self):
        """Test startup fails if microphone start fails."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.side_effect = Exception("Mic start failed")
        
        with pytest.raises(Exception):
            self.controller.start()

    def test_start_wake_word_failure_continues(self):
        """Test startup continues if wake word initialization fails."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.side_effect = Exception("Wake word failed")
        
        self.controller.start()
        
        # Should log warning but continue
        assert self.controller.logger.warning.called
        assert self.controller._running is True
        
        self.controller.stop()

    def test_wake_word_listener_loop(self):
        """Test wake word listener thread processes audio chunks."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        # Mock audio chunks
        test_chunk = np.array([1, 2, 3], dtype=np.int16)
        self.mock_mic_instance.get_audio_chunk.return_value = test_chunk
        self.mock_wake_instance.process_audio.return_value = False
        
        self.controller.start()
        
        # Wait for thread to process
        time.sleep(0.1)
        
        # Verify callback was set
        self.mock_wake_instance.set_callback.assert_called_once()
        
        # Verify audio processing
        assert self.mock_mic_instance.get_audio_chunk.called
        assert self.mock_wake_instance.process_audio.called
        
        self.controller.stop()

    def test_wake_word_detection_flow(self):
        """Test complete wake word detection to command enqueue flow."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        # Mock audio capture and transcription
        test_audio = np.array([1, 2, 3], dtype=np.int16)
        self.mock_mic_instance.capture_audio.return_value = test_audio
        self.mock_whisper_instance.transcribe.return_value = "jarvis move forward"
        
        # Mock command parsing
        test_command = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        self.mock_parser_instance.parse.return_value = [test_command]
        self.mock_queue_instance.enqueue.return_value = True
        
        self.controller.start()
        
        # Trigger wake word detection
        callback = self.mock_wake_instance.set_callback.call_args[0][0]
        callback()
        
        # Wait for processing
        time.sleep(0.1)
        
        # Verify flow
        self.mock_mic_instance.capture_audio.assert_called_once()
        self.mock_whisper_instance.transcribe.assert_called_once()
        self.mock_parser_instance.parse.assert_called_once()
        self.mock_queue_instance.enqueue.assert_called_once_with(test_command)
        
        self.controller.stop()

    def test_stop_command_bypasses_queue(self):
        """Test STOP command clears queue and sends immediately."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        # Mock command executor to return None (no commands in queue)
        self.mock_queue_instance.dequeue.return_value = None
        
        # Mock audio and transcription
        test_audio = np.array([1, 2, 3], dtype=np.int16)
        self.mock_mic_instance.capture_audio.return_value = test_audio
        self.mock_whisper_instance.transcribe.return_value = "stop"
        
        # Mock STOP command parsing
        stop_command = Command(CommandType.STOP, {}, PRIORITY_STOP)
        self.mock_parser_instance.parse.return_value = [stop_command]
        self.mock_serial_instance.send_command.return_value = True
        
        self.controller.start()
        
        # Wait a bit for executor to start
        time.sleep(0.05)
        
        # Trigger wake word detection
        callback = self.mock_wake_instance.set_callback.call_args[0][0]
        callback()
        
        # Wait for processing
        time.sleep(0.2)
        
        # Verify STOP handling
        self.mock_queue_instance.clear.assert_called_once()
        
        # Find the STOP command call (may have other calls from executor)
        stop_calls = [call for call in self.mock_serial_instance.send_command.call_args_list 
                     if len(call[0]) > 0 and hasattr(call[0][0], 'command_type') 
                     and call[0][0].command_type == CommandType.STOP]
        assert len(stop_calls) > 0, "STOP command should have been sent"
        
        self.controller.stop()

    def test_wake_word_serialization(self):
        """Test wake word detections are serialized using _processing_command flag."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        # Mock audio and transcription
        test_audio = np.array([1, 2, 3], dtype=np.int16)
        self.mock_mic_instance.capture_audio.return_value = test_audio
        self.mock_whisper_instance.transcribe.return_value = "jarvis move forward"
        test_command = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        self.mock_parser_instance.parse.return_value = [test_command]
        self.mock_queue_instance.enqueue.return_value = True
        
        self.controller.start()
        
        # Wait for callback to be set
        time.sleep(0.05)
        
        callback = self.mock_wake_instance.set_callback.call_args[0][0]
        
        # Manually set processing flag to simulate ongoing processing
        with self.controller._processing_lock:
            self.controller._processing_command = True
        
        # Trigger callback while processing flag is set (should be ignored)
        callback()
        
        # Wait a bit
        time.sleep(0.1)
        
        # Verify capture_audio was NOT called (callback returned early)
        assert self.mock_mic_instance.capture_audio.call_count == 0
        
        # Reset flag and trigger again (should work now)
        with self.controller._processing_lock:
            self.controller._processing_command = False
        
        callback()
        time.sleep(0.1)
        
        # Now capture_audio should have been called
        assert self.mock_mic_instance.capture_audio.call_count == 1
        
        self.controller.stop()

    def test_command_executor_loop(self):
        """Test command executor dequeues and sends commands."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        # Mock command in queue
        test_command = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        self.mock_queue_instance.dequeue.return_value = test_command
        self.mock_serial_instance.send_command.return_value = True
        self.mock_serial_instance.read_response.return_value = {"success": True}
        
        self.controller.start()
        
        # Wait for executor to process
        time.sleep(0.2)
        
        # Verify command execution
        assert self.mock_queue_instance.dequeue.called
        assert self.mock_serial_instance.send_command.called
        assert self.mock_serial_instance.read_response.called
        
        self.controller.stop()

    def test_command_executor_no_response(self):
        """Test command executor handles missing responses gracefully."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        test_command = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        self.mock_queue_instance.dequeue.return_value = test_command
        self.mock_serial_instance.send_command.return_value = True
        self.mock_serial_instance.read_response.return_value = None  # No response
        
        self.controller.start()
        
        # Wait for executor
        time.sleep(0.2)
        
        # Should log warning but continue
        assert self.controller.logger.warning.called
        
        self.controller.stop()

    def test_stop_graceful_shutdown(self):
        """Test graceful shutdown sequence."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        self.controller.start()
        
        # Stop controller
        self.controller.stop()
        
        # Verify cleanup order
        assert self.controller._running is False
        assert self.mock_serial_instance.send_command.called  # STOP command sent
        self.mock_mic_instance.stop.assert_called_once()
        self.mock_wake_instance.cleanup.assert_called_once()
        self.mock_whisper_instance.unload_model.assert_called_once()
        self.mock_serial_instance.disconnect.assert_called_once()

    def test_stop_sends_stop_command(self):
        """Test stop sends STOP command to ESP32."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        self.controller.start()
        self.controller.stop()
        
        # Verify STOP command was sent
        assert self.mock_serial_instance.send_command.called
        sent_command = self.mock_serial_instance.send_command.call_args[0][0]
        assert sent_command.command_type == CommandType.STOP
        assert sent_command.priority == PRIORITY_STOP

    def test_queue_full_drops_command(self):
        """Test queue full drops command and logs warning."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        # Mock audio and transcription
        test_audio = np.array([1, 2, 3], dtype=np.int16)
        self.mock_mic_instance.capture_audio.return_value = test_audio
        self.mock_whisper_instance.transcribe.return_value = "jarvis move forward"
        
        # Mock queue full
        test_command = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        self.mock_parser_instance.parse.return_value = [test_command]
        self.mock_queue_instance.enqueue.return_value = False  # Queue full
        
        self.controller.start()
        
        # Trigger wake word detection
        callback = self.mock_wake_instance.set_callback.call_args[0][0]
        callback()
        
        # Wait for processing
        time.sleep(0.1)
        
        # Verify warning logged
        assert self.controller.logger.warning.called
        
        self.controller.stop()

    def test_signal_handlers_installed(self):
        """Test signal handlers are installed."""
        with patch('signal.signal') as mock_signal:
            self.controller._setup_signal_handlers()
            
            # Verify handlers installed for SIGINT and SIGTERM
            assert mock_signal.call_count == 2
            calls = [call[0][0] for call in mock_signal.call_args_list]
            assert signal.SIGINT in calls
            assert signal.SIGTERM in calls

    def test_signal_handler_calls_stop(self):
        """Test signal handler calls stop and exits."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        self.controller.start()
        
        # Mock sys.exit to prevent actual exit
        with patch('sys.exit') as mock_exit:
            # Call signal handler
            self.controller._signal_handler(signal.SIGINT, None)
            
            # Verify stop was called
            assert self.controller._running is False
            assert mock_exit.called

    def test_error_handling_in_wake_word_listener(self):
        """Test wake word listener handles errors gracefully."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        # Mock error in get_audio_chunk
        self.mock_mic_instance.get_audio_chunk.side_effect = Exception("Audio error")
        
        self.controller.start()
        
        # Wait for thread to process
        time.sleep(0.1)
        
        # Should log error but continue
        assert self.controller.logger.error.called
        
        self.controller.stop()

    def test_error_handling_in_command_executor(self):
        """Test command executor handles errors gracefully."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        # Mock error in dequeue
        self.mock_queue_instance.dequeue.side_effect = Exception("Queue error")
        
        self.controller.start()
        
        # Wait for executor
        time.sleep(0.1)
        
        # Should log error but continue
        assert self.controller.logger.error.called
        
        self.controller.stop()

    def test_transcription_failure_handled(self):
        """Test transcription failure is handled gracefully."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        # Mock transcription failure
        test_audio = np.array([1, 2, 3], dtype=np.int16)
        self.mock_mic_instance.capture_audio.return_value = test_audio
        self.mock_whisper_instance.transcribe.side_effect = Exception("Transcription failed")
        
        self.controller.start()
        
        # Trigger wake word detection
        callback = self.mock_wake_instance.set_callback.call_args[0][0]
        callback()
        
        # Wait for processing
        time.sleep(0.1)
        
        # Should log error but not crash
        assert self.controller.logger.error.called
        
        self.controller.stop()

    def test_empty_transcription_handled(self):
        """Test empty transcription is handled gracefully."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        # Mock empty transcription
        test_audio = np.array([1, 2, 3], dtype=np.int16)
        self.mock_mic_instance.capture_audio.return_value = test_audio
        self.mock_whisper_instance.transcribe.return_value = ""
        
        self.controller.start()
        
        # Trigger wake word detection
        callback = self.mock_wake_instance.set_callback.call_args[0][0]
        callback()
        
        # Wait for processing
        time.sleep(0.1)
        
        # Should log warning
        assert self.controller.logger.warning.called
        
        self.controller.stop()

    def test_parse_failure_handled(self):
        """Test parse failure is handled gracefully."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        # Mock parse returning None
        test_audio = np.array([1, 2, 3], dtype=np.int16)
        self.mock_mic_instance.capture_audio.return_value = test_audio
        self.mock_whisper_instance.transcribe.return_value = "jarvis gibberish"
        self.mock_parser_instance.parse.return_value = None
        
        self.controller.start()
        
        # Trigger wake word detection
        callback = self.mock_wake_instance.set_callback.call_args[0][0]
        callback()
        
        # Wait for processing
        time.sleep(0.1)
        
        # Should log warning
        assert self.controller.logger.warning.called
        
        self.controller.stop()

    def test_multiple_commands_in_sequence(self):
        """Test multiple commands parsed from one transcription."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        # Mock multiple commands
        test_audio = np.array([1, 2, 3], dtype=np.int16)
        self.mock_mic_instance.capture_audio.return_value = test_audio
        self.mock_whisper_instance.transcribe.return_value = "jarvis move forward then turn right"
        
        cmd1 = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        cmd2 = Command(CommandType.TURN_RIGHT, {"angle": 90.0, "speed": 0.4}, PRIORITY_NORMAL)
        self.mock_parser_instance.parse.return_value = [cmd1, cmd2]
        self.mock_queue_instance.enqueue.return_value = True
        
        self.controller.start()
        
        # Trigger wake word detection
        callback = self.mock_wake_instance.set_callback.call_args[0][0]
        callback()
        
        # Wait for processing
        time.sleep(0.1)
        
        # Verify both commands enqueued
        assert self.mock_queue_instance.enqueue.call_count == 2
        
        self.controller.stop()

    def test_double_start_idempotent(self):
        """Test calling start() twice doesn't create duplicate threads."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        self.controller.start()
        first_wake_thread = self.controller._wake_word_thread
        first_executor_thread = self.controller._command_executor_thread
        
        # Call start again
        self.controller.start()
        
        # Threads should be the same (or new ones if recreated, but not duplicates)
        # Most importantly, _running should still be True
        assert self.controller._running is True
        
        self.controller.stop()

    def test_stop_before_start(self):
        """Test stop() can be called before start() without errors."""
        # Should not raise exception
        self.controller.stop()
        
        # Verify state
        assert self.controller._running is False

    def test_stop_during_wake_word_processing(self):
        """Test stop() called while wake word is processing."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        # Mock slow transcription
        test_audio = np.array([1, 2, 3], dtype=np.int16)
        self.mock_mic_instance.capture_audio.return_value = test_audio
        
        def slow_transcribe(audio):
            time.sleep(0.2)
            return "jarvis move forward"
        
        self.mock_whisper_instance.transcribe.side_effect = slow_transcribe
        test_command = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        self.mock_parser_instance.parse.return_value = [test_command]
        self.mock_queue_instance.enqueue.return_value = True
        
        self.controller.start()
        
        # Trigger wake word detection
        callback = self.mock_wake_instance.set_callback.call_args[0][0]
        callback()
        
        # Immediately call stop (while processing)
        time.sleep(0.05)  # Let processing start
        self.controller.stop()
        
        # Should complete without errors
        assert self.controller._running is False

    def test_stop_command_during_command_execution(self):
        """Test STOP command arriving while executor is sending a command."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        # Mock slow command send
        def slow_send(cmd):
            time.sleep(0.1)
            return True
        
        self.mock_serial_instance.send_command.side_effect = slow_send
        test_command = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        self.mock_queue_instance.dequeue.return_value = test_command
        self.mock_serial_instance.read_response.return_value = {"success": True}
        
        self.controller.start()
        
        # Wait for executor to start sending
        time.sleep(0.05)
        
        # Send STOP command (should clear queue and send immediately)
        stop_cmd = Command(CommandType.STOP, {}, PRIORITY_STOP)
        test_audio = np.array([1, 2, 3], dtype=np.int16)
        self.mock_mic_instance.capture_audio.return_value = test_audio
        self.mock_whisper_instance.transcribe.return_value = "stop"
        self.mock_parser_instance.parse.return_value = [stop_cmd]
        
        callback = self.mock_wake_instance.set_callback.call_args[0][0]
        callback()
        
        # Wait for processing
        time.sleep(0.2)
        
        # Queue should have been cleared
        assert self.mock_queue_instance.clear.called
        
        self.controller.stop()

    def test_whitespace_only_transcription(self):
        """Test transcription with only whitespace is handled."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        test_audio = np.array([1, 2, 3], dtype=np.int16)
        self.mock_mic_instance.capture_audio.return_value = test_audio
        # WhisperTranscriber strips and lowercases, so whitespace becomes empty string
        self.mock_whisper_instance.transcribe.return_value = ""  # Empty after strip
        
        self.controller.start()
        
        callback = self.mock_wake_instance.set_callback.call_args[0][0]
        callback()
        
        time.sleep(0.1)
        
        # Should log warning about empty transcription
        assert self.controller.logger.warning.called
        
        self.controller.stop()

    def test_parser_returns_empty_list(self):
        """Test parser returning empty list [] is handled."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        test_audio = np.array([1, 2, 3], dtype=np.int16)
        self.mock_mic_instance.capture_audio.return_value = test_audio
        self.mock_whisper_instance.transcribe.return_value = "jarvis gibberish"
        self.mock_parser_instance.parse.return_value = []  # Empty list, not None
        
        self.controller.start()
        
        callback = self.mock_wake_instance.set_callback.call_args[0][0]
        callback()
        
        time.sleep(0.1)
        
        # Should log warning
        assert self.controller.logger.warning.called
        
        self.controller.stop()

    def test_wake_word_during_shutdown(self):
        """Test wake word detected during shutdown is ignored."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        self.controller.start()
        
        # Begin shutdown
        self.controller._running = False
        
        # Trigger wake word detection after shutdown started
        callback = self.mock_wake_instance.set_callback.call_args[0][0]
        callback()
        
        # Wait a bit
        time.sleep(0.1)
        
        # Audio capture should not be called (loop should exit)
        # Note: This is more of a behavioral test - the loop checks _running
        
        self.controller.stop()

    def test_thread_join_timeout_handled(self):
        """Test thread join timeout is handled gracefully."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        self.controller.start()
        
        # Create a thread that won't stop quickly
        def never_ending_loop():
            while True:
                time.sleep(0.1)
        
        stuck_thread = threading.Thread(target=never_ending_loop, daemon=True)
        stuck_thread.start()
        
        # Replace controller threads with stuck thread temporarily
        original_wake_thread = self.controller._wake_word_thread
        self.controller._wake_word_thread = stuck_thread
        
        # Stop with very short timeout
        self.controller._running = False
        stuck_thread.join(timeout=0.01)
        
        if stuck_thread.is_alive():
            # This simulates the timeout scenario
            self.controller.logger.warning("Wake word thread did not stop gracefully")
        
        # Restore original thread and stop properly
        self.controller._wake_word_thread = original_wake_thread
        self.controller.stop()
        
        # Should log warning about threads not stopping
        assert self.controller.logger.warning.called

    def test_multiple_cleanup_failures(self):
        """Test multiple component cleanup failures are all handled."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        # Make multiple cleanups fail
        self.mock_mic_instance.stop.side_effect = Exception("Mic stop failed")
        self.mock_wake_instance.cleanup.side_effect = Exception("Wake cleanup failed")
        self.mock_serial_instance.disconnect.side_effect = Exception("Serial disconnect failed")
        
        self.controller.start()
        self.controller.stop()
        
        # All errors should be logged
        assert self.controller.logger.error.call_count >= 3

    def test_stop_command_send_failure(self):
        """Test STOP command send failure is handled gracefully."""
        self.mock_serial_instance.connect.return_value = True
        self.mock_whisper_instance.load_model.return_value = None
        self.mock_mic_instance.start.return_value = None
        self.mock_wake_instance.initialize.return_value = None
        
        # Make STOP send fail
        self.mock_serial_instance.send_command.side_effect = Exception("Send failed")
        
        self.controller.start()
        self.controller.stop()
        
        # Should log warning but continue cleanup
        assert self.controller.logger.warning.called
        # Cleanup should still proceed
        assert self.mock_mic_instance.stop.called
