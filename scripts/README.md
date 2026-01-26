# Test Scripts

Quick reference for testing command parser and related functionality.

## Interactive Command Parser

Test command sequences interactively:

```bash
source venv/bin/activate
python scripts/test_parser_interactive.py
```

Or test a single command:

```bash
python scripts/test_parser_interactive.py "jarvis, move forward, turn right"
```

**Interactive Mode Examples:**
```
> jarvis, move forward fast
✓ Parsed 1 command(s):
  [1] move_forward(speed=0.7) [priority: 0]

> jarvis, move forward, turn left slowly, make a circle
✓ Parsed 3 command(s):
  [1] move_forward(speed=0.4) [priority: 0]
  [2] turn_left(angle=90.0, speed=0.2) [priority: 0]
  [3] make_circle(radius=0.5, speed=0.4, direction=left) [priority: 0]

> stop
✓ Parsed 1 command(s):
  [1] stop() [priority: STOP]

> quit
```

## Audio File Testing

Test with actual audio files:

```bash
python scripts/test_audio_files.py
```

Test specific audio file:

```bash
python scripts/test_audio_files.py tests/pi/audio_samples/single_command.wav
```

## Quick Test Examples

```bash
# Single command
python scripts/test_parser_interactive.py "move forward"

# Multiple commands
python scripts/test_parser_interactive.py "jarvis, move forward, turn right"

# With modifiers
python scripts/test_parser_interactive.py "move forward fast, turn left slowly"

# Intermediate commands
python scripts/test_parser_interactive.py "jarvis, make a circle, make a square"

# Stop command
python scripts/test_parser_interactive.py "stop"
```
