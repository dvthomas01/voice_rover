"""Tests for size modifiers in shape commands."""

import pytest
from pi.command_parser.parser import CommandParser
from pi.command_parser.command_schema import CommandType


class TestSizeModifiers:
    """Test cases for size modifiers in shape commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CommandParser()

    def test_make_square_large(self):
        """Test 'make a large square'."""
        cmd = self.parser.parse("jarvis make a large square")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.MAKE_SQUARE
        assert cmd[0].parameters["side_length"] == 0.8
        assert cmd[0].parameters["speed"] == 0.4

    def test_make_square_small(self):
        """Test 'make a small square'."""
        cmd = self.parser.parse("jarvis make a small square")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.MAKE_SQUARE
        assert cmd[0].parameters["side_length"] == 0.3

    def test_make_circle_large(self):
        """Test 'make a large circle'."""
        cmd = self.parser.parse("jarvis make a large circle")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.MAKE_CIRCLE
        assert cmd[0].parameters["radius"] == 0.8

    def test_make_circle_small(self):
        """Test 'make a small circle'."""
        cmd = self.parser.parse("jarvis make a small circle")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.MAKE_CIRCLE
        assert cmd[0].parameters["radius"] == 0.3

    def test_make_star_large(self):
        """Test 'make a large star'."""
        cmd = self.parser.parse("jarvis make a large star")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.MAKE_STAR
        assert cmd[0].parameters["size"] == 0.8

    def test_make_star_small(self):
        """Test 'make a small star'."""
        cmd = self.parser.parse("jarvis make a small star")
        assert cmd is not None
        assert cmd[0].command_type == CommandType.MAKE_STAR
        assert cmd[0].parameters["size"] == 0.3

    def test_make_square_tiny(self):
        """Test 'make a tiny square'."""
        cmd = self.parser.parse("jarvis make a tiny square")
        assert cmd is not None
        assert cmd[0].parameters["side_length"] == 0.2

    def test_make_circle_huge(self):
        """Test 'make a huge circle'."""
        cmd = self.parser.parse("jarvis make a huge circle")
        assert cmd is not None
        assert cmd[0].parameters["radius"] == 1.0

    def test_make_square_with_size_and_speed(self):
        """Test 'make a large square slowly'."""
        cmd = self.parser.parse("jarvis make a large square slowly")
        assert cmd is not None
        assert cmd[0].parameters["side_length"] == 0.8
        assert cmd[0].parameters["speed"] == 0.2

    def test_make_circle_with_size_and_speed(self):
        """Test 'make a large circle slowly'."""
        cmd = self.parser.parse("jarvis make a large circle slowly")
        assert cmd is not None
        assert cmd[0].parameters["radius"] == 0.8
        assert cmd[0].parameters["speed"] == 0.2
