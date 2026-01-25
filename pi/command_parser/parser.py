"""Natural language to structured command parser."""

import re
from typing import Dict, List, Optional, Any
from .command_schema import Command, CommandType, PRIORITY_STOP, PRIORITY_NORMAL


class CommandParser:
    """Parses natural language into structured commands."""

    DEFAULT_SPEED = 0.4
    DEFAULT_ANGLE = 90.0
    DEFAULT_DURATION = 1.0
    DEFAULT_SIDE_LENGTH = 0.5
    DEFAULT_RADIUS = 0.5
    DEFAULT_STAR_SIZE = 0.5
    DEFAULT_SEGMENT_LENGTH = 0.3
    DEFAULT_ZIGZAG_ANGLE = 45.0
    DEFAULT_ZIGZAG_REPETITIONS = 4
    DEFAULT_SPIN_DURATION = 2.0
    DEFAULT_SPIN_SPEED = 0.5

    SPEED_MODIFIERS = {
        "fast": 0.7,
        "slow": 0.2,
        "slowly": 0.2,
        "quickly": 0.7,
        "quick": 0.7,
        "rapidly": 0.8,
        "rapid": 0.8,
        "a bit faster": 0.6,
        "a bit slower": 0.3,
        "a bit quicker": 0.6,
        "very fast": 0.9,
        "very slow": 0.15,
        "very quickly": 0.9,
        "very slowly": 0.15,
    }

    def __init__(self):
        """Initialize command parser."""
        self._synonyms = self._build_synonym_patterns()
        self._transition_words = ["then", "and", "then move", "then turn"]

    def _build_synonym_patterns(self) -> Dict[CommandType, List[str]]:
        """Build regex patterns for all command synonyms."""
        return {
            CommandType.MOVE_FORWARD: [
                r"move\s+forward",
                r"go\s+forward",
                r"forward",
                r"move\s+ahead",
                r"go\s+ahead",
            ],
            CommandType.MOVE_BACKWARD: [
                r"move\s+backward",
                r"go\s+backward",
                r"backward",
                r"back\s+up",
                r"reverse",
            ],
            CommandType.ROTATE_CLOCKWISE: [
                r"rotate\s+clockwise",
                r"turn\s+clockwise",
                r"spin\s+right",
                r"rotate\s+right",
            ],
            CommandType.ROTATE_COUNTERCLOCKWISE: [
                r"rotate\s+counterclockwise",
                r"rotate\s+counter\s+clockwise",
                r"turn\s+counterclockwise",
                r"turn\s+counter\s+clockwise",
                r"spin\s+left",
                r"rotate\s+left",
            ],
            CommandType.STOP: [
                r"stop",
                r"halt",
                r"emergency\s+stop",
                r"cease",
            ],
            CommandType.TURN_LEFT: [
                r"turn\s+left",
                r"move\s+left",
            ],
            CommandType.TURN_RIGHT: [
                r"turn\s+right",
                r"move\s+right",
            ],
            CommandType.MOVE_FORWARD_FOR_TIME: [
                r"move\s+forward\s+for",
                r"go\s+forward\s+for",
            ],
            CommandType.MOVE_BACKWARD_FOR_TIME: [
                r"move\s+backward\s+for",
                r"go\s+backward\s+for",
            ],
            CommandType.MAKE_SQUARE: [
                r"make\s+a?\s*square",
                r"create\s+a?\s*square",
            ],
            CommandType.MAKE_CIRCLE: [
                r"make\s+a?\s*circle",
                r"create\s+a?\s*circle",
            ],
            CommandType.MAKE_STAR: [
                r"make\s+a?\s*star",
                r"create\s+a?\s*star",
            ],
            CommandType.ZIGZAG: [
                r"zigzag",
                r"zig\s+zag",
            ],
            CommandType.SPIN: [
                r"spin",
            ],
            CommandType.DANCE: [
                r"dance",
            ],
        }

    def parse(self, text: str) -> Optional[List[Command]]:
        """Parse natural language text into commands.

        Args:
            text: Natural language command text

        Returns:
            List of Command objects, or None if parsing fails
        """
        if not text or not text.strip():
            return None

        text = text.strip().lower()
        text = self._remove_wake_word(text)
        
        if not text:
            return None

        segments = self._split_commands(text)
        commands = []

        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue

            segment_commands = self._parse_segment_commands(segment)
            if segment_commands:
                commands.extend(segment_commands)

        return commands if commands else None

    def _parse_segment_commands(self, text: str) -> List[Command]:
        """Parse all commands from a segment, handling multiple commands in one segment.
        
        This handles cases like "move forward fast turn left slowly" where
        multiple commands appear without transition words.
        """
        commands = []
        remaining_text = text
        
        while remaining_text.strip():
            best_match = None
            best_start = len(remaining_text)
            best_end = 0
            angle_match_info = None
            
            turn_clockwise_with_angle = re.search(
                r"(?:turn|rotate)\s+clockwise(?:\s+(\d+(?:\.\d+)?)\s*degrees?)",
                remaining_text,
                re.IGNORECASE
            )
            if turn_clockwise_with_angle and turn_clockwise_with_angle.group(1):
                if turn_clockwise_with_angle.start() < best_start:
                    best_match = (CommandType.ROTATE_CLOCKWISE, turn_clockwise_with_angle)
                    best_start = turn_clockwise_with_angle.start()
                    best_end = turn_clockwise_with_angle.end()
                    angle_match_info = ("clockwise", float(turn_clockwise_with_angle.group(1)))

            turn_counterclockwise_with_angle = re.search(
                r"(?:turn|rotate)\s+counter\s*clockwise(?:\s+(\d+(?:\.\d+)?)\s*degrees?)",
                remaining_text,
                re.IGNORECASE
            )
            if turn_counterclockwise_with_angle and turn_counterclockwise_with_angle.group(1):
                if turn_counterclockwise_with_angle.start() < best_start:
                    best_match = (CommandType.ROTATE_COUNTERCLOCKWISE, turn_counterclockwise_with_angle)
                    best_start = turn_counterclockwise_with_angle.start()
                    best_end = turn_counterclockwise_with_angle.end()
                    angle_match_info = ("counterclockwise", float(turn_counterclockwise_with_angle.group(1)))

            turn_with_angle_no_direction = re.search(
                r"(?:turn|rotate)(?!\s+(?:clockwise|counter\s*clockwise|left|right))\s+(\d+(?:\.\d+)?)\s*degrees?",
                remaining_text,
                re.IGNORECASE
            )
            if turn_with_angle_no_direction and turn_with_angle_no_direction.group(1):
                if turn_with_angle_no_direction.start() < best_start:
                    best_match = (CommandType.ROTATE_COUNTERCLOCKWISE, turn_with_angle_no_direction)
                    best_start = turn_with_angle_no_direction.start()
                    best_end = turn_with_angle_no_direction.end()
                    angle_match_info = ("counterclockwise", float(turn_with_angle_no_direction.group(1)))

            for cmd_type in [CommandType.TURN_LEFT, CommandType.TURN_RIGHT, 
                            CommandType.MOVE_FORWARD_FOR_TIME, CommandType.MOVE_BACKWARD_FOR_TIME,
                            CommandType.MAKE_SQUARE, CommandType.MAKE_CIRCLE, 
                            CommandType.MAKE_STAR, CommandType.ZIGZAG, CommandType.SPIN, 
                            CommandType.DANCE]:
                patterns = self._synonyms.get(cmd_type, [])
                for pattern in patterns:
                    match = re.search(pattern, remaining_text, re.IGNORECASE)
                    if match and match.start() < best_start:
                        extended_end = self._extend_match_for_parameters(remaining_text, match.end())
                        best_match = (cmd_type, match)
                        best_start = match.start()
                        best_end = extended_end
            
            for cmd_type in [CommandType.MOVE_FORWARD, CommandType.MOVE_BACKWARD,
                            CommandType.ROTATE_CLOCKWISE, CommandType.ROTATE_COUNTERCLOCKWISE,
                            CommandType.STOP]:
                patterns = self._synonyms.get(cmd_type, [])
                for pattern in patterns:
                    match = re.search(pattern, remaining_text, re.IGNORECASE)
                    if match and match.start() < best_start:
                        best_match = (cmd_type, match)
                        best_start = match.start()
                        best_end = match.end()
            
            if not best_match:
                break
            
            cmd_type, match = best_match
            command_text = remaining_text[best_start:best_end]
            
            command_with_modifier = self._extract_command_with_modifier(
                remaining_text, best_start, best_end
            )
            
            if angle_match_info:
                direction, angle = angle_match_info
                speed = self._extract_speed(command_with_modifier, self.DEFAULT_SPEED)
                if direction == "counterclockwise":
                    cmd = Command(CommandType.ROTATE_COUNTERCLOCKWISE, {"angle": angle, "speed": speed}, PRIORITY_NORMAL)
                else:
                    cmd = Command(CommandType.ROTATE_CLOCKWISE, {"angle": angle, "speed": speed}, PRIORITY_NORMAL)
            elif cmd_type in [CommandType.TURN_LEFT, CommandType.TURN_RIGHT]:
                cmd = self._parse_intermediate(command_with_modifier)
            elif cmd_type in [CommandType.MOVE_FORWARD_FOR_TIME, CommandType.MOVE_BACKWARD_FOR_TIME,
                          CommandType.MAKE_SQUARE, CommandType.MAKE_CIRCLE,
                          CommandType.MAKE_STAR, CommandType.ZIGZAG, CommandType.SPIN,
                          CommandType.DANCE]:
                cmd = self._parse_intermediate(command_with_modifier)
            else:
                cmd = self._parse_primitive(command_with_modifier)
            
            if cmd:
                commands.append(cmd)
            
            remaining_text = remaining_text[best_end:].strip()
        
        return commands

    def _remove_wake_word(self, text: str) -> str:
        """Remove wake word from text if present."""
        text = re.sub(r"^jarvis\s*,?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^hey\s+jarvis\s*,?\s*", "", text, flags=re.IGNORECASE)
        return text.strip()

    def _split_commands(self, text: str) -> List[str]:
        """Split text into individual command segments."""
        segments = re.split(r",\s*", text)
        
        new_segments = []
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue
            
            for transition in self._transition_words:
                if re.search(rf"\b{re.escape(transition)}\b", segment, re.IGNORECASE):
                    parts = re.split(rf"\b{re.escape(transition)}\b", segment, flags=re.IGNORECASE)
                    new_segments.extend([p.strip() for p in parts if p.strip()])
                    break
            else:
                new_segments.append(segment)
        
        return new_segments if new_segments else [text]

    def _parse_single_command(self, text: str) -> Optional[Command]:
        """Parse a single command segment."""
        text = text.strip()
        if not text:
            return None

        cmd = self._parse_intermediate(text)
        if cmd:
            return cmd

        cmd = self._parse_primitive(text)
        if cmd:
            return cmd

        return None

    def _parse_primitive(self, text: str) -> Optional[Command]:
        """Parse primitive command."""
        speed = self._extract_speed(text, self.DEFAULT_SPEED)

        if self._matches_pattern(text, CommandType.MOVE_FORWARD):
            return Command(
                CommandType.MOVE_FORWARD,
                {"speed": speed},
                PRIORITY_NORMAL
            )

        if self._matches_pattern(text, CommandType.MOVE_BACKWARD):
            return Command(
                CommandType.MOVE_BACKWARD,
                {"speed": speed},
                PRIORITY_NORMAL
            )

        if self._matches_pattern(text, CommandType.ROTATE_CLOCKWISE):
            return Command(
                CommandType.ROTATE_CLOCKWISE,
                {"speed": speed},
                PRIORITY_NORMAL
            )

        if self._matches_pattern(text, CommandType.ROTATE_COUNTERCLOCKWISE):
            return Command(
                CommandType.ROTATE_COUNTERCLOCKWISE,
                {"speed": speed},
                PRIORITY_NORMAL
            )

        if self._matches_pattern(text, CommandType.STOP):
            return Command(
                CommandType.STOP,
                {},
                PRIORITY_STOP
            )

        return None

    def _parse_intermediate(self, text: str) -> Optional[Command]:
        """Parse intermediate command."""
        speed = self._extract_speed(text, self.DEFAULT_SPEED)


        turn_left_match = re.search(r"(?:turn|move)\s+left(?:\s+(\d+(?:\.\d+)?)\s*degrees?)?", text)
        if turn_left_match:
            angle = float(turn_left_match.group(1)) if turn_left_match.group(1) else self.DEFAULT_ANGLE
            return Command(
                CommandType.TURN_LEFT,
                {"angle": angle, "speed": speed},
                PRIORITY_NORMAL
            )

        turn_right_match = re.search(r"(?:turn|move)\s+right(?:\s+(\d+(?:\.\d+)?)\s*degrees?)?", text)
        if turn_right_match:
            angle = float(turn_right_match.group(1)) if turn_right_match.group(1) else self.DEFAULT_ANGLE
            return Command(
                CommandType.TURN_RIGHT,
                {"angle": angle, "speed": speed},
                PRIORITY_NORMAL
            )

        forward_time_match = re.search(
            r"(?:move|go)\s+forward\s+for\s+(\d+(?:\.\d+)?)\s*seconds?",
            text
        )
        if forward_time_match:
            duration = float(forward_time_match.group(1))
            return Command(
                CommandType.MOVE_FORWARD_FOR_TIME,
                {"duration": duration, "speed": speed},
                PRIORITY_NORMAL
            )

        backward_time_match = re.search(
            r"(?:move|go)\s+backward\s+for\s+(\d+(?:\.\d+)?)\s*seconds?",
            text
        )
        if backward_time_match:
            duration = float(backward_time_match.group(1))
            return Command(
                CommandType.MOVE_BACKWARD_FOR_TIME,
                {"duration": duration, "speed": speed},
                PRIORITY_NORMAL
            )

        if self._matches_pattern(text, CommandType.MAKE_SQUARE):
            side_length = self._extract_number(text, "side", self.DEFAULT_SIDE_LENGTH)
            return Command(
                CommandType.MAKE_SQUARE,
                {"side_length": side_length, "speed": speed},
                PRIORITY_NORMAL
            )

        if self._matches_pattern(text, CommandType.MAKE_CIRCLE):
            radius = self._extract_number(text, "radius", self.DEFAULT_RADIUS)
            direction_match = re.search(r"(left|right|counterclockwise|clockwise)", text)
            direction = "left" if direction_match and direction_match.group(1) in ["left", "counterclockwise"] else "left"
            if direction_match and direction_match.group(1) in ["right", "clockwise"]:
                direction = "right"
            return Command(
                CommandType.MAKE_CIRCLE,
                {"radius": radius, "speed": speed, "direction": direction},
                PRIORITY_NORMAL
            )

        if self._matches_pattern(text, CommandType.MAKE_STAR):
            size = self._extract_number(text, "size", self.DEFAULT_STAR_SIZE)
            return Command(
                CommandType.MAKE_STAR,
                {"size": size, "speed": speed},
                PRIORITY_NORMAL
            )

        if self._matches_pattern(text, CommandType.ZIGZAG):
            segment_length = self._extract_number(text, "segment", self.DEFAULT_SEGMENT_LENGTH)
            angle = self._extract_number(text, "angle", self.DEFAULT_ZIGZAG_ANGLE)
            repetitions = int(self._extract_number(text, "repetitions", self.DEFAULT_ZIGZAG_REPETITIONS))
            return Command(
                CommandType.ZIGZAG,
                {"segment_length": segment_length, "angle": angle, "repetitions": repetitions, "speed": speed},
                PRIORITY_NORMAL
            )

        if self._matches_pattern(text, CommandType.SPIN):
            duration_match = re.search(r"for\s+(\d+(?:\.\d+)?)\s*seconds?", text)
            duration = float(duration_match.group(1)) if duration_match else self.DEFAULT_SPIN_DURATION
            spin_speed = self._extract_speed(text, self.DEFAULT_SPIN_SPEED)
            return Command(
                CommandType.SPIN,
                {"duration": duration, "speed": spin_speed},
                PRIORITY_NORMAL
            )

        if self._matches_pattern(text, CommandType.DANCE):
            return Command(
                CommandType.DANCE,
                {},
                PRIORITY_NORMAL
            )

        return None

    def _matches_pattern(self, text: str, command_type: CommandType) -> bool:
        """Check if text matches any pattern for command type."""
        patterns = self._synonyms.get(command_type, [])
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _extract_speed(self, text: str, default: float = DEFAULT_SPEED) -> float:
        """Extract speed parameter from text.
        
        Checks for explicit speed values first, then modifiers.
        Modifiers are checked in order (longer phrases first to avoid partial matches).
        """
        explicit_match = re.search(r"(?:at\s+)?speed\s*[:\s]*(\d+\.?\d*)", text)
        if explicit_match:
            speed = float(explicit_match.group(1))
            return max(0.0, min(1.0, speed))

        sorted_modifiers = sorted(self.SPEED_MODIFIERS.items(), key=lambda x: len(x[0]), reverse=True)
        for modifier, value in sorted_modifiers:
            if re.search(rf"\b{re.escape(modifier)}\b", text, re.IGNORECASE):
                return value

        return default

    def _extract_number(self, text: str, keyword: str, default: float) -> float:
        """Extract number parameter from text."""
        pattern = rf"{re.escape(keyword)}\s*[:\s]*(\d+\.?\d*)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return default

    def _extend_match_for_parameters(self, text: str, end_pos: int) -> int:
        """Extend match end position to include parameters like angles, durations, etc."""
        remaining = text[end_pos:].strip()
        
        angle_match = re.search(r"^\s*(\d+(?:\.\d+)?)\s*degrees?", remaining, re.IGNORECASE)
        if angle_match:
            return end_pos + angle_match.end()
        
        duration_match = re.search(r"^\s*for\s+(\d+(?:\.\d+)?)\s*seconds?", remaining, re.IGNORECASE)
        if duration_match:
            return end_pos + duration_match.end()
        
        speed_match = re.search(r"^\s*at\s+speed\s+(\d+(?:\.\d+)?)", remaining, re.IGNORECASE)
        if speed_match:
            return end_pos + speed_match.end()
        
        return end_pos

    def _extract_command_with_modifier(self, text: str, start: int, end: int) -> str:
        """Extract command text with its associated modifier.
        
        Finds the command and any modifier immediately before or after it,
        but not modifiers from other commands in the same segment.
        Includes the full command match (which may extend beyond start:end for parameters).
        """
        extended_end = self._extend_match_for_parameters(text, end)
        
        modifier_window_start = max(0, start - 12)
        modifier_window_end = min(len(text), extended_end + 12)
        modifier_window = text[modifier_window_start:modifier_window_end]
        
        command_with_modifier = modifier_window
        
        modifier_found = False
        for modifier in sorted(self.SPEED_MODIFIERS.keys(), key=len, reverse=True):
            modifier_pattern = rf"\b{re.escape(modifier)}\b"
            modifier_match = re.search(modifier_pattern, modifier_window, re.IGNORECASE)
            if modifier_match:
                modifier_pos_in_window = modifier_match.start()
                modifier_pos_in_text = modifier_window_start + modifier_pos_in_window
                command_start = start
                command_end = extended_end
                
                if (modifier_pos_in_text >= command_start - 10 and modifier_pos_in_text <= command_end + 10):
                    modifier_found = True
                    break
        
        if not modifier_found:
            command_with_modifier = modifier_window
        
        return command_with_modifier
