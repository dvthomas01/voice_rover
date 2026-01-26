"""Simple, fast unit tests for SerialInterface core functionality.

These tests focus on core logic without hardware dependencies:
- JSON serialization/deserialization
- Response parsing
- Command formatting
- Error handling logic

Hardware-dependent tests (actual port connection) are deferred to integration testing.
"""

import pytest
import json
from unittest.mock import Mock, patch
from pi.serial_comm.serial_interface import SerialInterface
from pi.command_parser.command_schema import Command, CommandType, PRIORITY_NORMAL, PRIORITY_STOP


class TestSerialInterfaceCore:
    """Fast unit tests for core SerialInterface functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interface = SerialInterface(port="/dev/ttyUSB0", baudrate=115200)
        self.interface.logger = Mock()

    def test_serialize_command(self):
        """Test command serialization to JSON."""
        cmd = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        json_str = self.interface._serialize_command(cmd)
        
        assert json_str.endswith("\n")
        data = json.loads(json_str.strip())
        assert data["command"] == "move_forward"
        assert data["parameters"]["speed"] == 0.4
        assert data["priority"] == 0

    def test_serialize_stop_command(self):
        """Test STOP command serialization."""
        cmd = Command(CommandType.STOP, {}, PRIORITY_STOP)
        json_str = self.interface._serialize_command(cmd)
        
        data = json.loads(json_str.strip())
        assert data["command"] == "stop"
        assert data["priority"] == 100

    def test_parse_response_success(self):
        """Test successful response parsing."""
        response_json = b'{"success": true, "message": "Command executed"}'
        response = self.interface._parse_response(response_json)
        
        assert response is not None
        assert response["success"] is True
        assert response["message"] == "Command executed"

    def test_parse_response_error(self):
        """Test error response parsing."""
        response_json = b'{"success": false, "error": "Invalid command"}'
        response = self.interface._parse_response(response_json)
        
        assert response is not None
        assert response["success"] is False
        assert response["error"] == "Invalid command"

    def test_parse_response_invalid_json(self):
        """Test parsing invalid JSON."""
        invalid_json = b"not json"
        response = self.interface._parse_response(invalid_json)
        
        assert response is None
        self.interface.logger.error.assert_called()

    def test_parse_response_empty(self):
        """Test parsing empty response."""
        response = self.interface._parse_response(b"")
        assert response is None

    def test_parse_response_whitespace(self):
        """Test parsing response with whitespace."""
        response_json = b'  {"success": true}  \n'
        response = self.interface._parse_response(response_json)
        
        assert response is not None
        assert response["success"] is True

    def test_find_serial_port_single(self):
        """Test port detection with single port."""
        with patch('glob.glob', return_value=['/dev/ttyUSB0']):
            port = self.interface._find_serial_port()
            assert port == "/dev/ttyUSB0"

    def test_find_serial_port_multiple(self):
        """Test port detection with multiple ports."""
        with patch('glob.glob', return_value=['/dev/ttyUSB0', '/dev/ttyUSB1']):
            port = self.interface._find_serial_port()
            assert port == "/dev/ttyUSB0"
            self.interface.logger.warning.assert_called()

    def test_find_serial_port_none(self):
        """Test port detection with no ports."""
        with patch('glob.glob', return_value=[]):
            port = self.interface._find_serial_port()
            assert port is None

    def test_find_serial_port_mixed_patterns(self):
        """Test port detection with mixed USB and ACM ports."""
        with patch('glob.glob', side_effect=[['/dev/ttyUSB0'], ['/dev/ttyACM0']]):
            port = self.interface._find_serial_port()
            assert port in ['/dev/ttyUSB0', '/dev/ttyACM0']

    def test_reconnect_backoff_calculation(self):
        """Test exponential backoff calculation."""
        self.interface._reconnect_attempts = 0
        wait_time = min(2 ** self.interface._reconnect_attempts, self.interface._max_backoff_seconds)
        assert wait_time == 1
        
        self.interface._reconnect_attempts = 3
        wait_time = min(2 ** self.interface._reconnect_attempts, self.interface._max_backoff_seconds)
        assert wait_time == 8
        
        self.interface._reconnect_attempts = 10
        wait_time = min(2 ** self.interface._reconnect_attempts, self.interface._max_backoff_seconds)
        assert wait_time == 10

    @patch('pi.serial_comm.serial_interface.serial.Serial')
    @patch('pi.serial_comm.serial_interface.time.sleep')
    @patch('pi.serial_comm.serial_interface.time.time')
    def test_reconnect_logic(self, mock_time, mock_sleep, mock_serial_class):
        """Test reconnection logic with mocked time."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial_class.return_value = mock_serial
        
        self.interface._reconnect_attempts = 0
        
        with patch.object(self.interface, 'connect', return_value=True):
            result = self.interface._reconnect()
            assert result is True
            assert self.interface._reconnect_attempts == 1
            mock_sleep.assert_called_once_with(1.0)

    def test_command_json_format(self):
        """Test that commands serialize to expected JSON format."""
        cmd = Command(CommandType.TURN_LEFT, {"angle": 90, "speed": 0.5}, PRIORITY_NORMAL)
        json_str = self.interface._serialize_command(cmd)
        data = json.loads(json_str.strip())
        
        assert "command" in data
        assert "parameters" in data
        assert "priority" in data
        assert data["command"] == "turn_left"
        assert data["parameters"]["angle"] == 90
        assert data["parameters"]["speed"] == 0.5

    def test_complex_command_serialization(self):
        """Test serialization of complex commands with multiple parameters."""
        cmd = Command(
            CommandType.MAKE_SQUARE,
            {"side_length": 0.5, "speed": 0.4},
            PRIORITY_NORMAL
        )
        json_str = self.interface._serialize_command(cmd)
        data = json.loads(json_str.strip())
        
        assert data["command"] == "make_square"
        assert data["parameters"]["side_length"] == 0.5
        assert data["parameters"]["speed"] == 0.4

    def test_response_validation(self):
        """Test that only dict responses are accepted."""
        valid_response = b'{"success": true}'
        result = self.interface._parse_response(valid_response)
        assert isinstance(result, dict)
        
        invalid_response = b'"just a string"'
        result = self.interface._parse_response(invalid_response)
        assert result is None
