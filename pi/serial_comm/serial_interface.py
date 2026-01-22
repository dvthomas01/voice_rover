"""USB serial communication interface to ESP32."""

from typing import Optional, Dict, Any
import json
from ..command_parser.command_schema import Command


class SerialInterface:
    """Handles serial communication with ESP32."""

    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 115200):
        """Initialize serial interface.

        Args:
            port: Serial port path
            baudrate: Communication baud rate
        """
        self.port = port
        self.baudrate = baudrate
        self._serial = None
        self._connected = False

    def connect(self) -> bool:
        """Establish serial connection to ESP32.

        Returns:
            True if connection successful, False otherwise
        """
        raise NotImplementedError("To be implemented")

    def disconnect(self) -> None:
        """Close serial connection."""
        raise NotImplementedError("To be implemented")

    def send_command(self, command: Command) -> bool:
        """Send command to ESP32.

        Args:
            command: Command object to send

        Returns:
            True if sent successfully, False otherwise
        """
        raise NotImplementedError("To be implemented")

    def read_response(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """Read response from ESP32.

        Args:
            timeout: Maximum time to wait for response

        Returns:
            Response dictionary, or None if timeout/error
        """
        raise NotImplementedError("To be implemented")

    def is_connected(self) -> bool:
        """Check if serial connection is active.

        Returns:
            True if connected
        """
        return self._connected

    def _serialize_command(self, command: Command) -> str:
        """Convert command to JSON string for transmission.

        Args:
            command: Command to serialize

        Returns:
            JSON string with newline terminator
        """
        return json.dumps(command.to_json()) + "\n"
