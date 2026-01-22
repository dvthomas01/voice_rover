"""Unit tests for command parser module."""

import pytest
from pi.command_parser.parser import CommandParser
from pi.command_parser.command_schema import Command, CommandType


class TestCommandParser:
    """Test cases for CommandParser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CommandParser()

    def test_parse_forward_command(self):
        """Test parsing a forward movement command."""
        # To be implemented
        pass

    def test_parse_turn_command(self):
        """Test parsing a turn command."""
        # To be implemented
        pass

    def test_parse_stop_command(self):
        """Test parsing a stop command."""
        # To be implemented
        pass

    def test_parse_intermediate_command(self):
        """Test parsing an intermediate command that expands to primitives."""
        # To be implemented
        pass

    def test_invalid_command(self):
        """Test handling of invalid commands."""
        # To be implemented
        pass

    def test_command_priority(self):
        """Test that STOP command has highest priority."""
        # To be implemented
        pass
