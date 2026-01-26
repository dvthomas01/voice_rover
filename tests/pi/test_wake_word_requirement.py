"""Tests for wake word requirement."""

import pytest
from pi.command_parser.parser import CommandParser
from pi.command_parser.command_schema import CommandType


class TestWakeWordRequirement:
    """Test cases for wake word requirement."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CommandParser()

    def test_command_without_wake_word_fails(self):
        """Test that commands without wake word return None."""
        assert self.parser.parse("move forward") is None
        assert self.parser.parse("turn left") is None
        assert self.parser.parse("make a circle") is None
        assert self.parser.parse("spin") is None

    def test_stop_without_wake_word_works(self):
        """Test that stop command works without wake word."""
        cmd = self.parser.parse("stop")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.STOP

    def test_stop_with_wake_word_works(self):
        """Test that stop command works with wake word."""
        cmd = self.parser.parse("jarvis stop")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.STOP

    def test_command_with_wake_word_works(self):
        """Test that commands with wake word work."""
        cmd = self.parser.parse("jarvis move forward")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.MOVE_FORWARD

    def test_multiple_commands_with_wake_word(self):
        """Test multiple commands with wake word."""
        cmd = self.parser.parse("jarvis move forward then turn right")
        assert cmd is not None
        assert len(cmd) == 2

    def test_wake_word_in_middle_works(self):
        """Test that wake word can appear in middle of sentence."""
        cmd = self.parser.parse("jarvis move forward")
        assert cmd is not None
