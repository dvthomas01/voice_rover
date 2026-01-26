# Command Parser & Queue Manager Implementation Plan

## Overview

Implementation plan for command parser and queue manager functionality. This covers pre-hardware development work that can be completed before the hackathon starts.

**Target**: Complete, robust, demo-ready implementation with comprehensive testing
**Timeline**: Before hardware arrives (before hackathon)
**Branch**: `dami` (parallel development)

---

## Requirements Summary

### Command Parsing Requirements

1. **Sequence Parsing**: Parse full sentences with multiple commands
   - "Jarvis, move forward, then turn right" → [move_forward, turn_right]
   - "Jarvis, move forward, turn right" → [move_forward, turn_right] (no "then" required)
   - Commands queued in order they appear in sentence

2. **Ambiguity Handling**: Map synonyms to canonical commands
   - "move forward" = "go forward"
   - "turn left" = "turn 90 degrees counterclockwise"
   - "turn right" = "turn 90 degrees clockwise"

3. **Speed Modifiers**: Relative to default (0.4)
   - "fast" → higher speed (e.g., 0.6)
   - "slow" → lower speed (e.g., 0.2)
   - "a bit faster" → slightly higher (e.g., 0.5)
   - Modifiers only apply to the command they're attached to

4. **Stop Command**: Always accepted, with or without wake word
   - "Stop" → STOP command (priority 100)
   - "Jarvis, stop" → STOP command (priority 100)

5. **Turn Commands**: Default to 90 degrees
   - "turn left" → turn_left(angle=90, speed=0.4)
   - "turn right" → turn_right(angle=90, speed=0.4)
   - Explicit angles: "turn left 45 degrees" → turn_left(angle=45, speed=0.4)

6. **Intermediate Commands**: Send to ESP32 as-is (don't expand on Pi)
   - "make a circle" → make_circle command (not expanded to primitives)
   - ESP32 handles expansion

7. **Error Handling**: Return None/empty list for ambiguous cases
   - Silent failure, no error messages

### Queue Manager Requirements

1. **Priority Queue**: FIFO with priority handling
2. **STOP Priority**: STOP command (priority 100) always dequeues first
3. **Thread Safety**: All operations must be thread-safe
4. **Queue Clearing**: STOP command clears queue

---

## Implementation Plan

### Phase 1: Command Parser Core (4-5 hours)

#### 1.1 Pattern Matching System
**File**: `pi/command_parser/parser.py`

**Tasks**:
- Create synonym dictionary mapping common phrases to canonical commands
- Implement regex pattern matching for all command types
- Handle case-insensitive matching
- Support multiple phrasings for same command

**Synonym Mappings**:
```python
MOVE_FORWARD_SYNONYMS = [
    "move forward", "go forward", "forward", "move ahead", "go ahead"
]
MOVE_BACKWARD_SYNONYMS = [
    "move backward", "go backward", "backward", "back up", "reverse"
]
TURN_LEFT_SYNONYMS = [
    "turn left", "rotate left", "spin left", "turn counterclockwise"
]
TURN_RIGHT_SYNONYMS = [
    "turn right", "rotate right", "spin right", "turn clockwise"
]
STOP_SYNONYMS = [
    "stop", "halt", "emergency stop", "cease"
]
```

**Estimated Time**: 1-2 hours

#### 1.2 Sequence Parsing
**File**: `pi/command_parser/parser.py`

**Tasks**:
- Parse full sentence to extract multiple commands
- Handle comma-separated commands
- Handle "then" as optional separator (ignore it)
- Extract commands in order they appear
- Return list of Command objects

**Algorithm**:
1. Remove wake word ("jarvis") if present
2. Split by commas and transition words ("then", "and", "then move")
3. For each segment, attempt to parse as command
4. Collect all successfully parsed commands
5. Return list (or None if no commands found)

**Example**:
```python
"jarvis, move forward, then turn right"
→ Remove "jarvis, "
→ Split: ["move forward", "then turn right"]
→ Parse: [move_forward, turn_right]
→ Return: [Command(MOVE_FORWARD, {...}), Command(TURN_RIGHT, {...})]
```

**Estimated Time**: 1-2 hours

#### 1.3 Parameter Extraction
**File**: `pi/command_parser/parser.py`

**Tasks**:
- Extract speed parameter (default: 0.4)
- Extract angle parameter (default: 90 for turn left/right)
- Extract duration parameter (for time-based commands)
- Extract pattern parameters (side_length, radius, etc.)
- Handle explicit parameters: "at speed 0.6", "for 2 seconds", "45 degrees"

**Speed Modifier Mapping** (relative to default 0.4):
```python
SPEED_MODIFIERS = {
    "fast": 0.6,           # +50%
    "slow": 0.2,           # -50%
    "slowly": 0.2,
    "a bit faster": 0.5,   # +25%
    "a bit slower": 0.3,   # -25%
    "very fast": 0.8,      # +100%
    "very slow": 0.15,     # -62.5%
    # Add more as needed
}
```

**Estimated Time**: 1 hour

#### 1.4 Modifier Application
**File**: `pi/command_parser/parser.py`

**Tasks**:
- Detect speed modifiers in command text
- Apply modifier to speed parameter
- Modifier only affects the command it's attached to
- Handle multiple modifiers (take strongest/last)

**Example**:
```python
"move forward fast" → speed = 0.6
"move forward slowly" → speed = 0.2
"move forward, turn right" → move_forward(speed=0.6), turn_right(speed=0.4)
```

**Estimated Time**: 30 minutes

---

### Phase 2: Command Queue Manager (2-3 hours)

#### 2.1 Priority Queue Implementation
**File**: `pi/command_queue/queue_manager.py`

**Tasks**:
- Implement enqueue with priority handling
- Use negative priority (PriorityQueue is min-heap, we want max priority first)
- Thread-safe operations with locks
- Handle queue full condition

**Implementation**:
```python
def enqueue(self, command: Command) -> bool:
    with self._lock:
        if self._queue.full():
            return False
        # Use negative priority for max-heap behavior
        priority_tuple = (-command.priority, id(command), command)
        self._queue.put(priority_tuple, block=False)
        return True
```

**Estimated Time**: 1 hour

#### 2.2 Dequeue and Queue Operations
**File**: `pi/command_queue/queue_manager.py`

**Tasks**:
- Implement dequeue with timeout
- Implement clear() for STOP command
- Implement is_empty() and size() helpers
- Thread-safe operations

**Implementation**:
```python
def dequeue(self, timeout: Optional[float] = None) -> Optional[Command]:
    try:
        priority, _, command = self._queue.get(timeout=timeout)
        return command
    except queue.Empty:
        return None

def clear(self) -> None:
    with self._lock:
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
```

**Estimated Time**: 1 hour

#### 2.3 STOP Command Handling
**File**: `pi/command_queue/queue_manager.py`

**Tasks**:
- Ensure STOP command (priority 100) always dequeues first
- Clear queue when STOP received
- Thread-safe clear operation

**Estimated Time**: 30 minutes

---

### Phase 3: Integration and Edge Cases (2-3 hours)

#### 3.1 Edge Case Handling
**File**: `pi/command_parser/parser.py`

**Tasks**:
- Handle commands without wake word (e.g., "Stop")
- Handle empty/invalid input (return None)
- Handle partial matches (best effort or None)
- Handle modifier-only phrases ("fast" alone → None)

**Estimated Time**: 1 hour

#### 3.2 Command Validation
**File**: `pi/command_parser/parser.py`

**Tasks**:
- Validate extracted parameters (speed in 0.0-1.0 range)
- Validate angles (reasonable range, e.g., 0-360)
- Validate durations (positive numbers)
- Clamp values to valid ranges

**Estimated Time**: 30 minutes

#### 3.3 Integration with Main Controller
**File**: `pi/main_controller.py` (partial)

**Tasks**:
- Integrate parser with Whisper transcription output
- Handle sequence of commands from parser
- Enqueue all commands from sequence
- Handle STOP command bypass (send immediately, clear queue)

**Estimated Time**: 1 hour

---

### Phase 4: Comprehensive Testing (3-4 hours)

#### 4.1 Unit Tests - Command Parser
**File**: `tests/pi/test_command_parser.py`

**Test Cases**:

1. **Primitive Commands**:
   - "move forward" → move_forward(speed=0.4)
   - "go forward" → move_forward(speed=0.4) (synonym)
   - "move backward" → move_backward(speed=0.4)
   - "rotate clockwise" → rotate_clockwise(speed=0.4)
   - "turn left" → turn_left(angle=90, speed=0.4)
   - "turn right" → turn_right(angle=90, speed=0.4)

2. **Stop Command**:
   - "stop" → stop() (priority 100)
   - "jarvis, stop" → stop() (priority 100)
   - "halt" → stop() (synonym)

3. **Command Sequences**:
   - "jarvis, move forward, turn right" → [move_forward, turn_right]
   - "jarvis, move forward, then turn right" → [move_forward, turn_right]
   - "jarvis, move backward, then move right, then make a circle" → [move_backward, turn_right, make_circle]
   - "jarvis, move forward, make a star" → [move_forward, make_star]

4. **Speed Modifiers**:
   - "move forward fast" → move_forward(speed=0.6)
   - "move forward slowly" → move_forward(speed=0.2)
   - "move forward a bit faster" → move_forward(speed=0.5)
   - "move forward fast, turn right" → [move_forward(speed=0.6), turn_right(speed=0.4)]

5. **Explicit Parameters**:
   - "turn left 45 degrees" → turn_left(angle=45, speed=0.4)
   - "move forward at speed 0.7" → move_forward(speed=0.7)
   - "move forward for 2 seconds" → move_forward_for_time(duration=2.0, speed=0.4)

6. **Intermediate Commands**:
   - "make a circle" → make_circle(radius=0.5, speed=0.4, direction="left")
   - "make a square" → make_square(side_length=0.5, speed=0.4)
   - "make a star" → make_star(size=0.5, speed=0.4)
   - "zigzag" → zigzag(segment_length=0.3, angle=45, repetitions=4, speed=0.4)
   - "spin for 2 seconds" → spin(duration=2.0, speed=0.5)
   - "dance" → dance()

7. **Error Cases**:
   - "invalid command" → None
   - "" → None
   - "jarvis" (no command) → None
   - "move something" → None (ambiguous)

**Estimated Time**: 2 hours

#### 4.2 Unit Tests - Queue Manager
**File**: `tests/pi/test_queue_manager.py`

**Test Cases**:

1. **Basic Operations**:
   - Enqueue single command
   - Dequeue single command
   - Queue empty check
   - Queue size check

2. **Priority Ordering**:
   - STOP command (priority 100) dequeues first
   - Normal commands (priority 0) dequeued in FIFO order
   - Mixed priorities: STOP always first

3. **Thread Safety**:
   - Concurrent enqueue operations
   - Concurrent dequeue operations
   - Clear during operations

4. **Queue Full**:
   - Enqueue when full returns False
   - Queue respects max_size

5. **STOP Command**:
   - STOP clears queue
   - STOP dequeues immediately even if queue has other commands

**Estimated Time**: 1 hour

#### 4.3 Integration Tests with Audio Files
**File**: `tests/pi/test_parser_with_audio.py` (new)

**Test Strategy**:
- Use pre-recorded audio files (WAV format, 16kHz mono recommended)
- Files should contain various command phrasings
- Test end-to-end: Audio → Whisper → Parser → Queue

**Audio Test Cases** (you'll provide files):
1. "jarvis, move forward" (clear, single command)
2. "jarvis, move forward, then turn right" (sequence)
3. "jarvis, move forward fast" (with modifier)
4. "stop" (standalone, no wake word)
5. "jarvis, make a circle" (intermediate command)
6. "jarvis, move forward, make a star" (mixed commands)
7. Various phrasings with synonyms
8. Edge cases (mumbled, background noise, etc.)

**Implementation**:
```python
def test_parser_with_audio_file(audio_file_path):
    # Load audio file
    audio = load_audio(audio_file_path)
    
    # Transcribe with Whisper
    transcriber = WhisperTranscriber()
    text = transcriber.transcribe(audio)
    
    # Parse commands
    parser = CommandParser()
    commands = parser.parse(text)
    
    # Verify expected commands
    assert commands is not None
    assert len(commands) == expected_count
    # ... verify command types and parameters
```

**Estimated Time**: 1-2 hours

---

## Detailed Implementation Steps

### Step 1: Command Parser - Pattern Matching (2 hours)

**File**: `pi/command_parser/parser.py`

1. Create synonym dictionaries for all command types
2. Implement `_initialize_patterns()` to register all patterns
3. Implement `_match_command()` helper to find best match
4. Test with various phrasings

**Code Structure**:
```python
class CommandParser:
    def __init__(self):
        self._synonyms = {
            CommandType.MOVE_FORWARD: ["move forward", "go forward", ...],
            CommandType.MOVE_BACKWARD: ["move backward", "go backward", ...],
            # ... etc
        }
        self._speed_modifiers = {
            "fast": 0.6,
            "slow": 0.2,
            # ... etc
        }
```

### Step 2: Command Parser - Sequence Parsing (2 hours)

**File**: `pi/command_parser/parser.py`

1. Implement `_split_commands()` to separate multiple commands
2. Handle wake word removal
3. Handle transition words ("then", "and")
4. Parse each segment independently
5. Return list of commands

**Algorithm**:
```python
def parse(self, text: str) -> Optional[List[Command]]:
    # 1. Remove wake word
    text = self._remove_wake_word(text)
    
    # 2. Split into command segments
    segments = self._split_commands(text)
    
    # 3. Parse each segment
    commands = []
    for segment in segments:
        cmd = self._parse_single_command(segment)
        if cmd:
            commands.append(cmd)
    
    return commands if commands else None
```

### Step 3: Command Parser - Parameter Extraction (1.5 hours)

**File**: `pi/command_parser/parser.py`

1. Implement `_extract_speed()` with modifier support
2. Implement `_extract_angle()` with default 90 for turn left/right
3. Implement `_extract_duration()` for time-based commands
4. Implement `_extract_pattern_params()` for intermediate commands
5. Validate and clamp all parameters

### Step 4: Command Parser - Modifier Handling (1 hour)

**File**: `pi/command_parser/parser.py`

1. Detect speed modifiers in command text
2. Apply modifier to speed parameter
3. Ensure modifier only affects attached command
4. Handle modifier precedence (if multiple found)

### Step 5: Queue Manager - Core Operations (2 hours)

**File**: `pi/command_queue/queue_manager.py`

1. Implement `enqueue()` with priority handling
2. Implement `dequeue()` with timeout
3. Implement `clear()` for STOP command
4. Implement `is_empty()` and `size()`
5. Add thread safety with locks

### Step 6: Testing - Unit Tests (2 hours)

**Files**: `tests/pi/test_command_parser.py`, `tests/pi/test_queue_manager.py`

1. Write comprehensive unit tests
2. Test all command types and phrasings
3. Test sequence parsing
4. Test modifier application
5. Test queue priority and thread safety
6. Achieve >90% code coverage

### Step 7: Testing - Audio Integration (1-2 hours)

**File**: `tests/pi/test_parser_with_audio.py` (new)

1. Set up audio file loading
2. Integrate with Whisper transcriber
3. Test with provided audio files
4. Verify parser handles real transcription output
5. Test edge cases (noise, mumbling, etc.)

---

## Testing Strategy

### Unit Testing (No Audio Needed)

**Command Parser**:
- Test with text input directly
- Test all command types
- Test all synonyms
- Test sequence parsing
- Test parameter extraction
- Test modifier application
- Test error cases

**Queue Manager**:
- Test priority ordering
- Test thread safety
- Test queue operations
- Test STOP command handling

### Integration Testing (With Audio)

**Recommended Approach**: Pre-recorded audio files

**Why Pre-recorded Files**:
- ✅ Reproducible tests
- ✅ Can test edge cases easily
- ✅ Don't depend on microphone availability
- ✅ Faster test execution
- ✅ Can test with various audio qualities
- ✅ Can test Whisper transcription accuracy

**Audio File Requirements**:
- Format: WAV (16kHz, mono, 16-bit) - matches Whisper input
- Content: Various command phrasings
- Quality: Clear recordings for baseline, noisy for edge cases
- Duration: 2-5 seconds per command

**Test Process**:
1. You provide audio files with known expected commands
2. Tests load audio → Whisper transcribes → Parser parses → Verify commands
3. Test both successful cases and edge cases

**Alternative**: If you want live testing, we can add a separate test script that uses your MacBook Pro microphone, but pre-recorded files are recommended for automated testing.

---

## Success Criteria

### Command Parser
- [ ] Parses all primitive commands correctly
- [ ] Handles all synonyms (move/go forward, turn left/right, etc.)
- [ ] Parses command sequences correctly
- [ ] Extracts parameters correctly (speed, angle, duration)
- [ ] Applies speed modifiers correctly
- [ ] Handles STOP command (with/without wake word)
- [ ] Returns None for ambiguous/invalid commands
- [ ] Handles edge cases gracefully

### Queue Manager
- [ ] Enqueues commands correctly
- [ ] Dequeues in priority order (STOP first)
- [ ] Thread-safe operations
- [ ] Clears queue on STOP
- [ ] Handles queue full condition
- [ ] All helper methods work correctly

### Testing
- [ ] >90% code coverage
- [ ] All unit tests pass
- [ ] Audio integration tests pass with provided files
- [ ] Edge cases handled correctly
- [ ] Performance acceptable (<100ms parsing time)

---

## File Structure

```
pi/
├── command_parser/
│   ├── __init__.py
│   ├── command_schema.py          # ✅ Already complete
│   └── parser.py                  # ⏳ To implement
├── command_queue/
│   ├── __init__.py
│   └── queue_manager.py           # ⏳ To implement
└── ...

tests/
└── pi/
    ├── test_command_parser.py     # ⏳ To implement
    ├── test_queue_manager.py      # ⏳ To implement
    └── test_parser_with_audio.py  # ⏳ To create
    └── audio_samples/              # ⏳ You'll provide
        ├── single_command.wav
        ├── sequence.wav
        ├── with_modifier.wav
        └── ...
```

---

## Implementation Order

### Day 1 (4-5 hours)
1. Command parser pattern matching (2 hours)
2. Command parser sequence parsing (2 hours)
3. Basic unit tests for parser (1 hour)

### Day 2 (4-5 hours)
4. Parameter extraction and modifiers (2 hours)
5. Queue manager implementation (2 hours)
6. Queue manager tests (1 hour)

### Day 3 (3-4 hours)
7. Edge case handling (1 hour)
8. Integration tests (1 hour)
9. Audio file testing setup (1 hour)
10. Final testing and refinement (1 hour)

**Total Estimated Time**: 11-14 hours

---

## Next Steps

1. **Review this plan** - Confirm approach and timeline
2. **Provide audio files** - Record test cases for integration testing
3. **Start implementation** - Begin with command parser pattern matching
4. **Test incrementally** - Test each feature as it's implemented
5. **Iterate** - Refine based on test results

---

## Questions for You

1. **Speed Modifier Values**: Confirm the mapping I suggested (fast=0.6, slow=0.2, etc.) or provide your preferred values
2. **Audio Files**: When can you provide test audio files? (I can start with text-based tests first)
3. **Additional Synonyms**: Any other common phrasings you want to support?
4. **Intermediate Command Parameters**: Default values for make_circle, make_square, etc.?

Ready to proceed once you confirm the plan and provide any clarifications!
