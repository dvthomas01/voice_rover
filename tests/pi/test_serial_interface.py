"""Unit tests for SerialInterface."""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock, call
import serial
from pi.serial_comm.serial_interface import SerialInterface
from pi.command_parser.command_schema import Command, CommandType, PRIORITY_STOP, PRIORITY_NORMAL


class TestSerialInterface:
    """Test cases for SerialInterface."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interface = SerialInterface(port="/dev/ttyUSB0", baudrate=115200)
        self.interface.logger = Mock()

    def test_init(self):
        """Test initialization."""
        assert self.interface.port == "/dev/ttyUSB0"
        assert self.interface.baudrate == 115200
        assert not self.interface._connected
        assert self.interface._serial is None
        assert self.interface._read_buffer == b""

    @patch('pi.serial_comm.serial_interface.serial.Serial')
    def test_connect_success(self, mock_serial_class):
        """Test successful connection."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial_class.return_value = mock_serial
        
        result = self.interface.connect()
        
        assert result is True
        assert self.interface._connected is True
        assert self.interface._reconnect_attempts == 0
        mock_serial_class.assert_called_once()

    @patch('pi.serial_comm.serial_interface.serial.Serial')
    def test_connect_failure(self, mock_serial_class):
        """Test connection failure."""
        mock_serial_class.side_effect = serial.SerialException("Port not found")
        
        result = self.interface.connect()
        
        assert result is False
        assert self.interface._connected is False

    @patch('pi.serial_comm.serial_interface.serial.Serial')
    @patch('pi.serial_comm.serial_interface.glob.glob')
    def test_connect_auto_detect_port(self, mock_glob, mock_serial_class):
        """Test auto-detection of serial port."""
        interface = SerialInterface(port="", baudrate=115200)
        interface.logger = Mock()
        
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial_class.return_value = mock_serial
        mock_glob.return_value = ['/dev/ttyUSB0']
        
        result = interface.connect()
        assert result is True
        assert interface.port == "/dev/ttyUSB0"

    @patch('pi.serial_comm.serial_interface.serial.Serial')
    @patch('pi.serial_comm.serial_interface.glob.glob')
    def test_connect_auto_detect_no_ports(self, mock_glob, mock_serial_class):
        """Test auto-detection when no ports found."""
        interface = SerialInterface(port="", baudrate=115200)
        interface.logger = Mock()
        mock_glob.return_value = []
        
        with pytest.raises(serial.SerialException):
            interface.connect()

    @patch('pi.serial_comm.serial_interface.serial.Serial')
    @patch('pi.serial_comm.serial_interface.glob.glob')
    def test_connect_auto_detect_multiple_ports(self, mock_glob, mock_serial_class):
        """Test auto-detection with multiple ports."""
        interface = SerialInterface(port="", baudrate=115200)
        interface.logger = Mock()
        
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial_class.return_value = mock_serial
        mock_glob.return_value = ['/dev/ttyUSB0', '/dev/ttyUSB1']
        
        result = interface.connect()
        assert result is True
        assert interface.port == "/dev/ttyUSB0"
        interface.logger.warning.assert_called()

    @patch('pi.serial_comm.serial_interface.serial.Serial')
    def test_disconnect(self, mock_serial_class):
        """Test disconnection."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial_class.return_value = mock_serial
        
        self.interface.connect()
        self.interface.disconnect()
        
        assert not self.interface._connected
        mock_serial.close.assert_called_once()

    def test_serialize_command(self):
        """Test command serialization."""
        cmd = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        json_str = self.interface._serialize_command(cmd)
        
        assert json_str.endswith("\n")
        data = json.loads(json_str.strip())
        assert data["command"] == "move_forward"
        assert data["parameters"]["speed"] == 0.4
        assert data["priority"] == 0

    def test_parse_response_success(self):
        """Test successful response parsing."""
        response_json = '{"success": true, "message": "Command executed"}\n'
        response = self.interface._parse_response(response_json.encode('utf-8'))
        
        assert response is not None
        assert response["success"] is True
        assert response["message"] == "Command executed"

    def test_parse_response_failure(self):
        """Test response parsing with invalid JSON."""
        invalid_json = b"not json\n"
        response = self.interface._parse_response(invalid_json)
        
        assert response is None
        self.interface.logger.error.assert_called()

    def test_parse_response_empty(self):
        """Test parsing empty response."""
        response = self.interface._parse_response(b"\n")
        assert response is None

    @patch('pi.serial_comm.serial_interface.serial.Serial')
    def test_send_command_success(self, mock_serial_class):
        """Test successful command sending."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.write = Mock()
        mock_serial.flush = Mock()
        mock_serial_class.return_value = mock_serial
        
        self.interface.connect()
        
        cmd = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        result = self.interface.send_command(cmd)
        
        assert result is True
        mock_serial.write.assert_called_once()
        mock_serial.flush.assert_called_once()

    @patch('pi.serial_comm.serial_interface.serial.Serial')
    def test_send_command_not_connected(self, mock_serial_class):
        """Test sending command when not connected."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.write = Mock()
        mock_serial.flush = Mock()
        mock_serial_class.return_value = mock_serial
        
        cmd = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        result = self.interface.send_command(cmd)
        
        assert result is True
        assert self.interface._connected is True

    @patch('pi.serial_comm.serial_interface.serial.Serial')
    def test_send_command_write_error(self, mock_serial_class):
        """Test handling write error during send."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.write = Mock(side_effect=serial.SerialException("Write failed"))
        mock_serial.flush = Mock()
        mock_serial_class.return_value = mock_serial
        
        self.interface.connect()
        
        cmd = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
        
        with patch.object(self.interface, '_reconnect', return_value=False):
            result = self.interface.send_command(cmd)
            assert result is False

    @patch('pi.serial_comm.serial_interface.serial.Serial')
    @patch('pi.serial_comm.serial_interface.time.sleep')
    @patch('pi.serial_comm.serial_interface.time.time')
    def test_read_response_blocking_success(self, mock_time, mock_sleep, mock_serial_class):
        """Test blocking read with successful response."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.in_waiting = 50
        response_data = b'{"success": true, "message": "OK"}\n'
        mock_serial.read = Mock(return_value=response_data)
        mock_serial_class.return_value = mock_serial
        
        mock_time.side_effect = [0.0, 0.05]
        
        self.interface.connect()
        
        response = self.interface.read_response(blocking=True, timeout=1.0)
        
        assert response is not None
        assert response["success"] is True
        assert response["message"] == "OK"

    @patch('pi.serial_comm.serial_interface.serial.Serial')
    @patch('pi.serial_comm.serial_interface.time.sleep')
    @patch('pi.serial_comm.serial_interface.time.time')
    def test_read_response_blocking_timeout(self, mock_time, mock_sleep, mock_serial_class):
        """Test blocking read with timeout."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.in_waiting = 0
        mock_serial.read = Mock(return_value=b"")
        mock_serial_class.return_value = mock_serial
        
        mock_time.side_effect = [0.0, 0.05, 0.15]
        
        self.interface.connect()
        
        response = self.interface.read_response(blocking=True, timeout=0.1)
        
        assert response is None
        self.interface.logger.warning.assert_called()

    @patch('pi.serial_comm.serial_interface.serial.Serial')
    def test_read_response_non_blocking(self, mock_serial_class):
        """Test non-blocking read."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.in_waiting = 0
        mock_serial.read = Mock(return_value=b"")
        mock_serial_class.return_value = mock_serial
        
        self.interface.connect()
        
        response = self.interface.read_response(blocking=False)
        
        assert response is None

    @patch('pi.serial_comm.serial_interface.serial.Serial')
    @patch('pi.serial_comm.serial_interface.time.sleep')
    @patch('pi.serial_comm.serial_interface.time.time')
    def test_read_response_partial_json(self, mock_time, mock_sleep, mock_serial_class):
        """Test reading partial JSON that arrives in chunks."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial_class.return_value = mock_serial
        
        self.interface.connect()
        
        first_chunk = b'{"success": true, "message": "OK"'
        second_chunk = b'}\n'
        
        mock_serial.in_waiting = len(first_chunk)
        mock_serial.read = Mock(side_effect=[first_chunk, second_chunk])
        mock_time.side_effect = [0.0, 0.05, 0.1]
        
        response = self.interface.read_response(blocking=True, timeout=1.0)
        
        assert response is not None
        assert response["success"] is True

    @patch('pi.serial_comm.serial_interface.serial.Serial')
    def test_read_response_multiple_messages(self, mock_serial_class):
        """Test reading multiple messages from buffer."""
        mock_serial = Mock()
        mock_serial.is_open = True
        messages = b'{"success": true, "msg": "1"}\n{"success": true, "msg": "2"}\n'
        mock_serial.in_waiting = len(messages)
        mock_serial.read = Mock(return_value=messages)
        mock_serial_class.return_value = mock_serial
        
        self.interface.connect()
        
        response1 = self.interface.read_response(blocking=False)
        response2 = self.interface.read_response(blocking=False)
        
        assert response1 is not None
        assert response1["msg"] == "1"
        assert response2 is not None
        assert response2["msg"] == "2"

    @patch('pi.serial_comm.serial_interface.serial.Serial')
    @patch('time.sleep')
    def test_reconnect_exponential_backoff(self, mock_sleep, mock_serial_class):
        """Test reconnection with exponential backoff."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial_class.side_effect = [
            serial.SerialException("First fail"),
            mock_serial
        ]
        
        self.interface._reconnect_attempts = 0
        
        with patch.object(self.interface, 'connect', side_effect=[False, True]):
            result = self.interface._reconnect()
            assert result is True
            assert self.interface._reconnect_attempts == 1
            mock_sleep.assert_called_once_with(1.0)

    @patch('pi.serial_comm.serial_interface.serial.Serial')
    @patch('time.sleep')
    def test_reconnect_backoff_capped(self, mock_sleep, mock_serial_class):
        """Test that backoff is capped at maximum."""
        self.interface._reconnect_attempts = 5
        self.interface._max_backoff_seconds = 10
        
        with patch.object(self.interface, 'connect', return_value=False):
            self.interface._reconnect()
            mock_sleep.assert_called_once_with(10.0)

    def test_is_connected(self):
        """Test connection status check."""
        assert not self.interface.is_connected()
        
        with patch('pi.serial_comm.serial_interface.serial.Serial') as mock_serial_class:
            mock_serial = Mock()
            mock_serial.is_open = True
            mock_serial_class.return_value = mock_serial
            
            self.interface.connect()
            assert self.interface.is_connected()

    @patch('pi.serial_comm.serial_interface.serial.Serial')
    def test_thread_safety(self, mock_serial_class):
        """Test thread safety of serial operations."""
        import threading
        
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.write = Mock()
        mock_serial.flush = Mock()
        mock_serial.in_waiting = 0
        mock_serial.read = Mock(return_value=b"")
        mock_serial_class.return_value = mock_serial
        
        self.interface.connect()
        
        results = []
        
        def send_commands():
            for i in range(10):
                cmd = Command(CommandType.MOVE_FORWARD, {"speed": 0.4}, PRIORITY_NORMAL)
                result = self.interface.send_command(cmd)
                results.append(result)
        
        threads = [threading.Thread(target=send_commands) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert all(results)
        assert len(results) == 30
