"""Integration tests for command parser with various phrasings."""

import pytest
from pi.command_parser.parser import CommandParser
from pi.command_parser.command_schema import CommandType


class TestParserIntegration:
    """Integration tests for command parser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CommandParser()

    def test_example_use_cases(self):
        """Test example use cases from requirements."""
        test_cases = [
            ("jarvis, turn left", [CommandType.TURN_LEFT]),
            ("jarvis, move forward, then turn right", [CommandType.MOVE_FORWARD, CommandType.TURN_RIGHT]),
            ("jarvis, move backward, then move right, then make a circle", 
             [CommandType.MOVE_BACKWARD, CommandType.TURN_RIGHT, CommandType.MAKE_CIRCLE]),
            ("jarvis, move forward, make a star", [CommandType.MOVE_FORWARD, CommandType.MAKE_STAR]),
            ("stop", [CommandType.STOP]),
            ("jarvis, go backward", [CommandType.MOVE_BACKWARD]),
        ]

        for text, expected_types in test_cases:
            result = self.parser.parse(text)
            assert result is not None, f"Failed to parse: {text}"
            assert len(result) == len(expected_types), f"Wrong number of commands for: {text}"
            for i, expected_type in enumerate(expected_types):
                assert result[i].command_type == expected_type, \
                    f"Command {i} mismatch for: {text}"

    def test_synonym_variations(self):
        """Test various synonym phrasings."""
        forward_variations = [
            "jarvis move forward",
            "jarvis go forward",
            "jarvis forward",
            "jarvis move ahead",
        ]
        
        for text in forward_variations:
            result = self.parser.parse(text)
            assert result is not None
            assert result[0].command_type == CommandType.MOVE_FORWARD

    def test_speed_modifiers(self):
        """Test speed modifier application."""
        test_cases = [
            ("jarvis move forward fast", 0.7),
            ("jarvis move forward slow", 0.2),
            ("jarvis move forward a bit faster", 0.6),
            ("jarvis move forward", 0.4),
        ]

        for text, expected_speed in test_cases:
            result = self.parser.parse(text)
            assert result is not None
            assert result[0].parameters["speed"] == expected_speed

    def test_modifier_scope(self):
        """Test that modifiers only apply to attached command."""
        result = self.parser.parse("jarvis move forward fast, turn right")
        assert result is not None
        assert len(result) == 2
        assert result[0].parameters["speed"] == 0.7
        assert result[1].parameters["speed"] == 0.4

    def test_angle_defaults(self):
        """Test angle defaults for turn commands."""
        result = self.parser.parse("jarvis turn left")
        assert result is not None
        assert result[0].parameters["angle"] == 90.0

        result = self.parser.parse("jarvis turn right")
        assert result is not None
        assert result[0].parameters["angle"] == 90.0

    def test_explicit_angles(self):
        """Test explicit angle specification."""
        result = self.parser.parse("jarvis turn left 45 degrees")
        assert result is not None
        assert result[0].parameters["angle"] == 45.0

    def test_intermediate_commands_not_expanded(self):
        """Test that intermediate commands are not expanded."""
        result = self.parser.parse("jarvis make a circle")
        assert result is not None
        assert result[0].command_type == CommandType.MAKE_CIRCLE
        assert "radius" in result[0].parameters
        assert "speed" in result[0].parameters
        assert "direction" in result[0].parameters
