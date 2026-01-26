"""USB serial communication interface to ESP32.

INTEGRATION POINT: Main controller uses send_command() to send commands
INTEGRATION POINT: Command executor reads responses via read_response()
PROTOCOL: Newline-delimited JSON
BAUDRATE: 115200
STOP COMMAND: Bypasses queue, sent immediately
"""

from typing import Optional, Dict, Any
import json
import serial
import serial.tools.list_ports
import time
import threading
import logging
import glob
from ..command_parser.command_schema import Command, PRIORITY_STOP
from ..config import SERIAL_PORT, SERIAL_BAUDRATE, SERIAL_TIMEOUT


class SerialInterface:
    """Handles serial communication with ESP32."""

    def __init__(self, port: str = None, baudrate: int = None):
        """Initialize serial interface.

        Args:
            port: Serial port path (defaults to config, auto-detects if None)
            baudrate: Communication baud rate (defaults to config)
        """
        self.logger = logging.getLogger(__name__)
        self.port = port if port is not None and port != "" else SERIAL_PORT
        self._auto_detect = (port is None or port == "")
        self.baudrate = baudrate or SERIAL_BAUDRATE
        self._serial = None
        self._connected = False
        self._reconnect_attempts = 0
        self._max_backoff_seconds = 10
        self._read_buffer = b""
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """Establish serial connection to ESP32.

        Returns:
            True if connection successful, False otherwise
            
        Raises:
            serial.SerialException: If no serial ports found (unrecoverable init failure)
        """
        with self._lock:
            if self._connected and self._serial and self._serial.is_open:
                return True
            
            port = self.port
            if self._auto_detect:
                detected_port = self._find_serial_port()
                if not detected_port:
                    raise serial.SerialException(
                        "No serial ports found. Connect ESP32 and try again."
                    )
                port = detected_port
                self.port = port
                self.logger.info(f"Auto-detected serial port: {port}")
            
            try:
                self._serial = serial.Serial(
                    port=port,
                    baudrate=self.baudrate,
                    timeout=SERIAL_TIMEOUT,
                    write_timeout=SERIAL_TIMEOUT
                )
                self._connected = True
                self._reconnect_attempts = 0
                self._read_buffer = b""
                self.logger.info(f"Serial connection established: {port} @ {self.baudrate}")
                return True
            except serial.SerialException as e:
                self.logger.error(f"Serial connection failed: {e}")
                self._connected = False
                return False
            except Exception as e:
                self.logger.error(f"Unexpected error during connection: {e}")
                self._connected = False
                return False

    def disconnect(self) -> None:
        """Close serial connection."""
        with self._lock:
            if self._serial and self._serial.is_open:
                try:
                    self._serial.close()
                    self.logger.info("Serial connection closed")
                except Exception as e:
                    self.logger.error(f"Error closing serial connection: {e}")
            self._connected = False
            self._read_buffer = b""

    def send_command(self, command: Command) -> bool:
        """Send command to ESP32.

        Args:
            command: Command object to send

        Returns:
            True if sent successfully, False otherwise
            
        Note:
            STOP commands bypass queue and are sent immediately by caller.
            This method handles all commands uniformly.
        """
        with self._lock:
            if not self._connected:
                if not self.connect():
                    return False
            
            try:
                json_str = self._serialize_command(command)
                self._serial.write(json_str.encode('utf-8'))
                self._serial.flush()
                self.logger.debug(f"Sent command: {command.command_type.value}")
                return True
            except serial.SerialException as e:
                self.logger.error(f"Serial write error: {e}")
                self._connected = False
                if self._reconnect():
                    return self.send_command(command)
                return False
            except Exception as e:
                self.logger.error(f"Unexpected error sending command: {e}")
                return False

    def read_response(self, blocking: bool = True, timeout: float = None) -> Optional[Dict[str, Any]]:
        """Read response from ESP32.

        Args:
            blocking: If True, wait for response until timeout. If False, return immediately if no data.
            timeout: Maximum time to wait for response (defaults to config, only used if blocking=True)

        Returns:
            Response dictionary, or None if timeout/error/no data available
        """
        with self._lock:
            if not self._connected:
                return None
            
            timeout = timeout or SERIAL_TIMEOUT
            
            try:
                if blocking:
                    start_time = time.time()
                    iterations = 0
                    max_iterations = int(timeout * 100)
                    
                    while iterations < max_iterations:
                        if self._serial.in_waiting > 0:
                            data = self._serial.read(self._serial.in_waiting)
                            self._read_buffer += data
                        
                        if b'\n' in self._read_buffer:
                            line, self._read_buffer = self._read_buffer.split(b'\n', 1)
                            return self._parse_response(line)
                        
                        if time.time() - start_time >= timeout:
                            break
                        
                        time.sleep(0.01)
                        iterations += 1
                    
                    self.logger.warning(f"Read response timeout after {timeout}s")
                    return None
                else:
                    if self._serial.in_waiting > 0:
                        data = self._serial.read(self._serial.in_waiting)
                        self._read_buffer += data
                    
                    if b'\n' in self._read_buffer:
                        line, self._read_buffer = self._read_buffer.split(b'\n', 1)
                        return self._parse_response(line)
                    
                    return None
                    
            except serial.SerialException as e:
                self.logger.error(f"Serial read error: {e}")
                self._connected = False
                return None
            except Exception as e:
                self.logger.error(f"Unexpected error reading response: {e}")
                return None

    def is_connected(self) -> bool:
        """Check if serial connection is active.

        Returns:
            True if connected
        """
        with self._lock:
            return self._connected and (self._serial is not None and self._serial.is_open)

    def _serialize_command(self, command: Command) -> str:
        """Convert command to JSON string for transmission.

        Args:
            command: Command to serialize

        Returns:
            JSON string with newline terminator
        """
        return json.dumps(command.to_json()) + "\n"
    
    def _parse_response(self, line: bytes) -> Optional[Dict[str, Any]]:
        """Parse response line from ESP32.

        Args:
            line: Bytes containing JSON response (without newline)

        Returns:
            Parsed response dictionary, or None if parsing failed
        """
        try:
            text = line.decode('utf-8').strip()
            if not text:
                return None
            
            response = json.loads(text)
            
            if not isinstance(response, dict):
                self.logger.warning(f"Response is not a dictionary: {response}")
                return None
            
            return response
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}, line: {line}")
            return None
        except UnicodeDecodeError as e:
            self.logger.error(f"Failed to decode response: {e}, line: {line}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error parsing response: {e}")
            return None
    
    def _reconnect(self) -> bool:
        """Attempt to reconnect with exponential backoff.
        
        Retries indefinitely with exponential backoff capped at max_backoff_seconds.
        
        Returns:
            True if reconnection successful, False otherwise
        """
        wait_time = min(2 ** self._reconnect_attempts, self._max_backoff_seconds)
        self.logger.info(f"Attempting reconnection (attempt {self._reconnect_attempts + 1}, waiting {wait_time}s)...")
        time.sleep(wait_time)
        self._reconnect_attempts += 1
        
        result = self.connect()
        if result:
            self.logger.info("Reconnection successful")
        else:
            self.logger.warning(f"Reconnection failed, will retry with exponential backoff")
        
        return result
    
    def _find_serial_port(self) -> Optional[str]:
        """Auto-detect ESP32 serial port.

        Scans /dev/ttyUSB* and /dev/ttyACM* for available ports.
        If multiple ports found, returns first and logs warning.

        Returns:
            Port path if found, None otherwise
        """
        ports = []
        
        for pattern in ['/dev/ttyUSB*', '/dev/ttyACM*']:
            ports.extend(glob.glob(pattern))
        
        if not ports:
            return None
        
        if len(ports) > 1:
            self.logger.warning(
                f"Multiple serial ports found: {ports}. Using first: {ports[0]}"
            )
        
        return ports[0]
