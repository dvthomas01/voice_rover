"""Tests for turn commands without direction specification."""

import pytest
from pi.command_parser.parser import CommandParser
from pi.command_parser.command_schema import CommandType


class TestTurnNoDirection:
    """Test cases for turn commands without direction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CommandParser()

    def test_turn_with_angle_no_direction(self):
        """Test 'turn X degrees' defaults to counterclockwise."""
        cmd = self.parser.parse("jarvis turn 68 degrees")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.ROTATE_COUNTERCLOCKWISE
        assert cmd[0].parameters["angle"] == 68.0
        assert cmd[0].parameters["speed"] == 0.4

    def test_rotate_with_angle_no_direction(self):
        """Test 'rotate X degrees' defaults to counterclockwise."""
        cmd = self.parser.parse("jarvis rotate 45 degrees")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.ROTATE_COUNTERCLOCKWISE
        assert cmd[0].parameters["angle"] == 45.0

    def test_turn_with_angle_in_sequence(self):
        """Test 'turn X degrees' in command sequence."""
        cmd = self.parser.parse("jarvis turn 68 degrees then move forward quickly")
        assert cmd is not None
        assert len(cmd) == 2
        assert cmd[0].command_type == CommandType.ROTATE_COUNTERCLOCKWISE
        assert cmd[0].parameters["angle"] == 68.0
        assert cmd[1].command_type == CommandType.MOVE_FORWARD
        assert cmd[1].parameters["speed"] == 0.7

    def test_turn_clockwise_still_works(self):
        """Test explicit clockwise still works."""
        cmd = self.parser.parse("jarvis turn clockwise 45 degrees")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.ROTATE_CLOCKWISE
        assert cmd[0].parameters["angle"] == 45.0

    def test_turn_counterclockwise_still_works(self):
        """Test explicit counterclockwise still works."""
        cmd = self.parser.parse("jarvis turn counter clockwise 68 degrees")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.ROTATE_COUNTERCLOCKWISE
        assert cmd[0].parameters["angle"] == 68.0

    def test_turn_left_still_works(self):
        """Test 'turn left' still works."""
        cmd = self.parser.parse("jarvis turn left 30 degrees")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.TURN_LEFT
        assert cmd[0].parameters["angle"] == 30.0

    def test_turn_right_still_works(self):
        """Test 'turn right' still works."""
        cmd = self.parser.parse("jarvis turn right")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.TURN_RIGHT
        assert cmd[0].parameters["angle"] == 90.0
