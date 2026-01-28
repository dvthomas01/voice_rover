# Audio Test Samples

This directory contains audio files for testing the command parser with real Whisper transcriptions.

## Audio File Requirements

- **Format**: WAV
- **Sample Rate**: 16kHz (Whisper's native input)
- **Channels**: Mono
- **Bit Depth**: 16-bit

## Recommended Test Files

Create the following audio files for comprehensive testing:

1. **single_command.wav**
   - Content: "jarvis, move forward"
   - Expected: Single MOVE_FORWARD command

2. **sequence.wav**
   - Content: "jarvis, move forward, turn right"
   - Expected: [MOVE_FORWARD, TURN_RIGHT]

3. **sequence_with_then.wav**
   - Content: "jarvis, move forward, then turn right"
   - Expected: [MOVE_FORWARD, TURN_RIGHT]

4. **with_modifier.wav**
   - Content: "jarvis, move forward fast"
   - Expected: MOVE_FORWARD with speed=0.7

5. **stop_command.wav**
   - Content: "stop"
   - Expected: STOP command (no wake word)

6. **stop_with_wake_word.wav**
   - Content: "jarvis, stop"
   - Expected: STOP command

7. **intermediate_command.wav**
   - Content: "jarvis, make a circle"
   - Expected: MAKE_CIRCLE command

8. **mixed_commands.wav**
   - Content: "jarvis, move forward, make a star"
   - Expected: [MOVE_FORWARD, MAKE_STAR]

9. **complex_sequence.wav**
   - Content: "jarvis, move backward, then move right, then make a circle"
   - Expected: [MOVE_BACKWARD, TURN_RIGHT, MAKE_CIRCLE]

10. **synonyms.wav**
    - Content: "jarvis, go forward, create a square"
    - Expected: [MOVE_FORWARD, MAKE_SQUARE]

## Recording Tips

- Use clear, natural speech
- Record in quiet environment
- Speak at normal pace
- Include variations (fast/slow speech, background noise) for edge case testing

## Converting Audio Files

If you have audio in other formats, convert to WAV:

```bash
# Using ffmpeg
ffmpeg -i input.mp3 -ar 16000 -ac 1 -sample_fmt s16 output.wav

# Using sox
sox input.mp3 -r 16000 -c 1 -b 16 output.wav
```

## Testing

Run audio integration tests:

```bash
pytest tests/pi/test_audio_integration.py -v
```

Tests will skip if audio files are not present.
