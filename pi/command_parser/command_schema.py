"""Command schema definitions for voice_rover."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any


class CommandType(Enum):
    """Types of commands the rover can execute."""

    # Primitive commands (sent directly to ESP32)
    MOVE_FORWARD = "move_forward"
    MOVE_BACKWARD = "move_backward"
    ROTATE_CLOCKWISE = "rotate_clockwise"
    ROTATE_COUNTERCLOCKWISE = "rotate_counterclockwise"
    STOP = "stop"

    # Intermediate commands (expanded to primitives on Pi side)
    TURN_LEFT = "turn_left"
    TURN_RIGHT = "turn_right"
    MOVE_FORWARD_FOR_TIME = "move_forward_for_time"
    MOVE_BACKWARD_FOR_TIME = "move_backward_for_time"
    MAKE_SQUARE = "make_square"
    MAKE_CIRCLE = "make_circle"
    MAKE_STAR = "make_star"
    ZIGZAG = "zigzag"
    SPIN = "spin"

    # Advanced commands (expanded to sequences)
    DANCE = "dance"


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
