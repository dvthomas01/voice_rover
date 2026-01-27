"""Tests for adverb modifiers (slowly, quickly, rapidly, etc.)."""

import pytest
from pi.command_parser.parser import CommandParser
from pi.command_parser.command_schema import CommandType


class TestAdverbModifiers:
    """Test adverb modifiers in commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CommandParser()

    def test_slowly_adverb(self):
        """Test 'slowly' adverb modifier."""
        cmd = self.parser.parse("jarvis move forward slowly")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.MOVE_FORWARD
        assert cmd[0].parameters["speed"] == 0.2

    def test_quickly_adverb(self):
        """Test 'quickly' adverb modifier."""
        cmd = self.parser.parse("jarvis move forward quickly")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.MOVE_FORWARD
        assert cmd[0].parameters["speed"] == 0.7

    def test_rapidly_adverb(self):
        """Test 'rapidly' adverb modifier."""
        cmd = self.parser.parse("jarvis move forward rapidly")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.MOVE_FORWARD
        assert cmd[0].parameters["speed"] == 0.8

    def test_quick_adjective(self):
        """Test 'quick' adjective modifier."""
        cmd = self.parser.parse("jarvis turn right quick")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.TURN_RIGHT
        assert cmd[0].parameters["speed"] == 0.7

    def test_rapid_adjective(self):
        """Test 'rapid' adjective modifier."""
        cmd = self.parser.parse("jarvis move backward rapid")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.MOVE_BACKWARD
        assert cmd[0].parameters["speed"] == 0.8

    def test_multiple_commands_with_adverbs(self):
        """Test multiple commands with different adverb modifiers."""
        cmd = self.parser.parse("jarvis move forward fast turn left slowly")
        assert cmd is not None
        assert len(cmd) == 2
        assert cmd[0].command_type == CommandType.MOVE_FORWARD
        assert cmd[0].parameters["speed"] == 0.7
        assert cmd[1].command_type == CommandType.TURN_LEFT
        assert cmd[1].parameters["speed"] == 0.2

    def test_very_slowly(self):
        """Test 'very slowly' compound modifier."""
        cmd = self.parser.parse("jarvis move forward very slowly")
        assert cmd is not None
        assert cmd[0].parameters["speed"] == 0.15

    def test_very_quickly(self):
        """Test 'very quickly' compound modifier."""
        cmd = self.parser.parse("jarvis turn right very quickly")
        assert cmd is not None
        assert cmd[0].parameters["speed"] == 0.9
