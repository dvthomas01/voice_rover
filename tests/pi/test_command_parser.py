"""Unit tests for command parser module."""

import pytest
from pi.command_parser.parser import CommandParser
from pi.command_parser.command_schema import Command, CommandType, PRIORITY_STOP, PRIORITY_NORMAL


class TestCommandParser:
    """Test cases for CommandParser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CommandParser()

    def test_parse_forward_command(self):
        """Test parsing forward movement commands."""
        cmd = self.parser.parse("jarvis move forward")
        assert cmd is not None
        assert len(cmd) == 1
        assert cmd[0].command_type == CommandType.MOVE_FORWARD
        assert cmd[0].parameters["speed"] == 0.4
        assert cmd[0].priority == PRIORITY_NORMAL

    def test_parse_forward_synonyms(self):
        """Test forward command synonyms."""
        synonyms = ["go forward", "forward", "move ahead", "go ahead"]
        for text in synonyms:
            cmd = self.parser.parse(text)
            assert cmd is not None
            assert cmd[0].command_type == CommandType.MOVE_FORWARD

    def test_parse_backward_command(self):
        """Test parsing backward movement commands."""
        cmd = self.parser.parse("move backward")
        assert cmd is not None
        assert len(cmd) == 1
        assert cmd[0].command_type == CommandType.MOVE_BACKWARD
        assert cmd[0].parameters["speed"] == 0.4

    def test_parse_backward_synonyms(self):
        """Test backward command synonyms."""
        synonyms = ["go backward", "backward", "back up", "reverse"]
        for text in synonyms:
            cmd = self.parser.parse(text)
            assert cmd is not None
            assert cmd[0].command_type == CommandType.MOVE_BACKWARD

    def test_parse_rotate_clockwise(self):
        """Test parsing clockwise rotation."""
        cmd = self.parser.parse("rotate clockwise")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.ROTATE_CLOCKWISE

    def test_parse_rotate_counterclockwise(self):
        """Test parsing counterclockwise rotation."""
        cmd = self.parser.parse("rotate counterclockwise")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.ROTATE_COUNTERCLOCKWISE

    def test_parse_turn_left_default(self):
        """Test turn left defaults to 90 degrees."""
        cmd = self.parser.parse("turn left")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.TURN_LEFT
        assert cmd[0].parameters["angle"] == 90.0
        assert cmd[0].parameters["speed"] == 0.4

    def test_parse_turn_left_explicit_angle(self):
        """Test turn left with explicit angle."""
        cmd = self.parser.parse("turn left 45 degrees")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.TURN_LEFT
        assert cmd[0].parameters["angle"] == 45.0

    def test_parse_turn_right_default(self):
        """Test turn right defaults to 90 degrees."""
        cmd = self.parser.parse("turn right")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.TURN_RIGHT
        assert cmd[0].parameters["angle"] == 90.0

    def test_parse_stop_command(self):
        """Test parsing stop command."""
        cmd = self.parser.parse("stop")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.STOP
        assert cmd[0].priority == PRIORITY_STOP
        assert cmd[0].parameters == {}

    def test_parse_stop_without_wake_word(self):
        """Test stop command works without wake word."""
        cmd = self.parser.parse("stop")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.STOP

    def test_parse_stop_with_wake_word(self):
        """Test stop command works with wake word."""
        cmd = self.parser.parse("jarvis, stop")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.STOP

    def test_parse_sequence_with_then(self):
        """Test parsing command sequence with 'then'."""
        cmd = self.parser.parse("jarvis, move forward, then turn right")
        assert cmd is not None
        assert len(cmd) == 2
        assert cmd[0].command_type == CommandType.MOVE_FORWARD
        assert cmd[1].command_type == CommandType.TURN_RIGHT

    def test_parse_sequence_without_then(self):
        """Test parsing command sequence without 'then'."""
        cmd = self.parser.parse("jarvis, move forward, turn right")
        assert cmd is not None
        assert len(cmd) == 2
        assert cmd[0].command_type == CommandType.MOVE_FORWARD
        assert cmd[1].command_type == CommandType.TURN_RIGHT

    def test_parse_sequence_multiple_commands(self):
        """Test parsing multiple commands in sequence."""
        cmd = self.parser.parse("jarvis, move backward, then move right, then make a circle")
        assert cmd is not None
        assert len(cmd) == 3
        assert cmd[0].command_type == CommandType.MOVE_BACKWARD
        assert cmd[1].command_type == CommandType.TURN_RIGHT
        assert cmd[2].command_type == CommandType.MAKE_CIRCLE

    def test_parse_speed_modifier_fast(self):
        """Test speed modifier 'fast'."""
        cmd = self.parser.parse("move forward fast")
        assert cmd is not None
        assert cmd[0].parameters["speed"] == 0.7

    def test_parse_speed_modifier_slow(self):
        """Test speed modifier 'slow'."""
        cmd = self.parser.parse("move forward slow")
        assert cmd is not None
        assert cmd[0].parameters["speed"] == 0.2

    def test_parse_speed_modifier_a_bit_faster(self):
        """Test speed modifier 'a bit faster'."""
        cmd = self.parser.parse("move forward a bit faster")
        assert cmd is not None
        assert cmd[0].parameters["speed"] == 0.6

    def test_parse_speed_modifier_scope(self):
        """Test modifier only applies to attached command."""
        cmd = self.parser.parse("move forward fast, turn right")
        assert cmd is not None
        assert len(cmd) == 2
        assert cmd[0].parameters["speed"] == 0.7
        assert cmd[1].parameters["speed"] == 0.4

    def test_parse_explicit_speed(self):
        """Test explicit speed parameter."""
        cmd = self.parser.parse("move forward at speed 0.8")
        assert cmd is not None
        assert cmd[0].parameters["speed"] == 0.8

    def test_parse_move_forward_for_time(self):
        """Test move forward for time command."""
        cmd = self.parser.parse("move forward for 2 seconds")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.MOVE_FORWARD_FOR_TIME
        assert cmd[0].parameters["duration"] == 2.0
        assert cmd[0].parameters["speed"] == 0.4

    def test_parse_move_backward_for_time(self):
        """Test move backward for time command."""
        cmd = self.parser.parse("move backward for 1.5 seconds")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.MOVE_BACKWARD_FOR_TIME
        assert cmd[0].parameters["duration"] == 1.5

    def test_parse_make_square(self):
        """Test make square command."""
        cmd = self.parser.parse("make a square")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.MAKE_SQUARE
        assert cmd[0].parameters["side_length"] == 0.5
        assert cmd[0].parameters["speed"] == 0.4

    def test_parse_make_square_synonym(self):
        """Test make square with 'create' synonym."""
        cmd = self.parser.parse("create a square")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.MAKE_SQUARE

    def test_parse_make_circle(self):
        """Test make circle command."""
        cmd = self.parser.parse("make a circle")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.MAKE_CIRCLE
        assert cmd[0].parameters["radius"] == 0.5
        assert cmd[0].parameters["speed"] == 0.4
        assert cmd[0].parameters["direction"] == "left"

    def test_parse_make_circle_synonym(self):
        """Test make circle with 'create' synonym."""
        cmd = self.parser.parse("create a circle")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.MAKE_CIRCLE

    def test_parse_make_star(self):
        """Test make star command."""
        cmd = self.parser.parse("make a star")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.MAKE_STAR
        assert cmd[0].parameters["size"] == 0.5

    def test_parse_zigzag(self):
        """Test zigzag command."""
        cmd = self.parser.parse("zigzag")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.ZIGZAG
        assert cmd[0].parameters["segment_length"] == 0.3
        assert cmd[0].parameters["angle"] == 45.0
        assert cmd[0].parameters["repetitions"] == 4

    def test_parse_spin(self):
        """Test spin command."""
        cmd = self.parser.parse("spin for 2 seconds")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.SPIN
        assert cmd[0].parameters["duration"] == 2.0
        assert cmd[0].parameters["speed"] == 0.5

    def test_parse_dance(self):
        """Test dance command."""
        cmd = self.parser.parse("dance")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.DANCE
        assert cmd[0].parameters == {}

    def test_parse_mixed_commands(self):
        """Test mixed primitive and intermediate commands."""
        cmd = self.parser.parse("jarvis, move forward, make a star")
        assert cmd is not None
        assert len(cmd) == 2
        assert cmd[0].command_type == CommandType.MOVE_FORWARD
        assert cmd[1].command_type == CommandType.MAKE_STAR

    def test_parse_invalid_command(self):
        """Test handling of invalid commands."""
        cmd = self.parser.parse("invalid command")
        assert cmd is None

    def test_parse_empty_string(self):
        """Test handling of empty string."""
        cmd = self.parser.parse("")
        assert cmd is None

    def test_parse_only_wake_word(self):
        """Test handling of only wake word."""
        cmd = self.parser.parse("jarvis")
        assert cmd is None

    def test_parse_ambiguous_command(self):
        """Test handling of ambiguous commands."""
        cmd = self.parser.parse("move something")
        assert cmd is None

    def test_wake_word_removal(self):
        """Test wake word is properly removed."""
        cmd1 = self.parser.parse("jarvis, move forward")
        assert cmd1 is not None
        assert cmd1[0].command_type == CommandType.MOVE_FORWARD
        
        cmd2 = self.parser.parse("move forward")
        assert cmd2 is None

    def test_command_priority(self):
        """Test that STOP command has highest priority."""
        cmd = self.parser.parse("stop")
        assert cmd is not None
        assert cmd[0].priority == PRIORITY_STOP
