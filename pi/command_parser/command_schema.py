"""Command schema definitions for voice_rover."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any


class CommandType(Enum):
    """Types of commands the rover can execute."""

    # Primitive commands
    MOVE_FORWARD = "move_forward"
    MOVE_BACKWARD = "move_backward"
    TURN_LEFT = "turn_left"
    TURN_RIGHT = "turn_right"
    STOP = "stop"

    # Intermediate commands
    TURN_AROUND = "turn_around"
    CIRCLE = "circle"
    SQUARE = "square"


@dataclass
class Command:
    """Structured command representation."""

    command_type: CommandType
    parameters: Dict[str, Any]
    priority: int = 0  # Higher priority commands execute first (STOP has highest)

    def to_json(self) -> Dict[str, Any]:
        """Convert command to JSON format for serial transmission.

        Returns:
            Dictionary representation of command
        """
        return {
            "command": self.command_type.value,
            "parameters": self.parameters,
            "priority": self.priority
        }


# Priority levels
PRIORITY_STOP = 100
PRIORITY_NORMAL = 0
