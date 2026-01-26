# Pre-Hardware Development Guide

## What You Can Do NOW (Without Hardware)

These tasks can be completed before you have physical hardware and will save significant time during the hackathon.

---

## ✅ HIGH PRIORITY - Do These First

### 1. **Command Parser Implementation** (2-3 hours)
**File**: `pi/command_parser/parser.py`

**Why**: Core logic, fully testable without hardware

**What to implement**:
- Pattern matching for all command types
- Parameter extraction (speed, angle, duration, etc.)
- Intermediate command expansion to primitives
- Error handling for invalid commands

**How to test**:
- Unit tests with various phrasings
- Test with sample text inputs
- Verify command expansion logic

**Example test cases**:
```python
"move forward" → move_forward(speed=0.4)
"turn left 90 degrees" → turn_left(angle=90, speed=0.4)
"move forward for 2 seconds" → move_forward_for_time(duration=2.0, speed=0.4)
"make a square" → [move_forward, turn_right, move_forward, turn_right, ...]
```

---

### 2. **Command Queue Manager** (1-2 hours)
**File**: `pi/command_queue/queue_manager.py`

**Why**: Thread-safe logic, fully testable

**What to implement**:
- PriorityQueue operations (enqueue, dequeue)
- Thread-safe locking
- STOP command priority handling
- Queue clearing

**How to test**:
- Unit tests for priority ordering
- Thread safety tests
- STOP command clearing tests

---

### 3. **Serial Interface (Mock Testing)** (2-3 hours)
**File**: `pi/serial_comm/serial_interface.py`

**Why**: Can test JSON serialization/deserialization without hardware

**What to implement**:
- JSON command serialization
- Response parsing
- Error handling
- Reconnection logic structure

**How to test**:
- Mock serial port (use `pytest-mock`)
- Test JSON formatting
- Test error handling
- Test with loopback (connect TX to RX on ESP32 if you have one)

---

### 4. **Command Handler JSON Parsing** (2-3 hours)
**File**: `esp32/src/command_handler/command_handler.cpp`

**Why**: Pure logic, no hardware dependencies

**What to implement**:
- JSON parsing with ArduinoJson
- Command validation (type, parameters, ranges)
- Parameter extraction and type checking
- Response generation

**How to test**:
- Unit tests with sample JSON strings
- Test validation logic
- Test error handling for malformed JSON

**Example test JSON**:
```json
{"command": "move_forward", "parameters": {"speed": 0.4}, "priority": 0}
{"command": "turn_left", "parameters": {"angle": 90, "speed": 0.5}, "priority": 0}
{"command": "stop", "parameters": {}, "priority": 100}
```

---

### 5. **Balance Controller PID Algorithm** (2-3 hours)
**File**: `esp32/src/balance/balance_controller.cpp`

**Why**: Pure math, can test with mock data

**What to implement**:
- PID calculation (P, I, D terms)
- Integral windup protection
- Setpoint modification (velocity, rotation)
- Output clamping

**How to test**:
- Unit tests with mock angle/velocity inputs
- Test PID math correctness
- Test integral windup limits
- Test setpoint modifications

**Test with mock data**:
```cpp
// Test with known inputs
float angle = 5.0;  // 5 degrees forward
float angular_velocity = 2.0;  // 2 deg/s
// Verify PID output is reasonable
```

---

### 6. **Test Infrastructure Setup** (2-3 hours)
**Files**: `tests/pi/`, `tests/esp32/`

**Why**: Enables testing everything else

**What to create**:
- Mock hardware interfaces
- Test fixtures
- Sample test data
- Test utilities

**Mock interfaces needed**:
- Mock serial port
- Mock IMU (return test angles)
- Mock encoders (return test pulses)
- Mock motors (verify commands)

---

## ✅ MEDIUM PRIORITY - Good to Have

### 7. **Main Controller Structure** (1-2 hours)
**File**: `pi/main_controller.py`

**Why**: Threading structure, can test logic flow

**What to implement**:
- Thread management structure
- Signal handling
- Error recovery logic
- Logging setup

**How to test**:
- Test thread creation/cleanup
- Test signal handling
- Mock all hardware dependencies

---

### 8. **Audio Pipeline (with any USB mic or files)** (2-3 hours)
**Files**: `pi/audio_input/microphone.py`, `pi/wake_word/detector.py`, `pi/whisper/transcriber.py`

**Why**: Can test with any USB microphone or audio files

**What to implement**:
- PyAudio setup (works with any USB mic)
- Audio capture and buffering
- Wake word detection (test with audio files)
- Whisper transcription (test with audio files)

**How to test**:
- Use any USB microphone (doesn't have to be Samson Go Mic)
- Test with pre-recorded audio files
- Test wake word with sample audio
- Test Whisper with sample audio files

**Note**: You can use ANY USB microphone for development - doesn't need to be the exact model.

---

### 9. **Configuration and Environment Setup** (1 hour)
**Files**: All config files

**Why**: Get dependencies installed and environment ready

**What to do**:
- Install all Python dependencies
- Install PlatformIO
- Set up Porcupine access key
- Download Whisper models (happens automatically on first use)
- Set up development environment

---

## ❌ WAIT FOR HARDWARE - Don't Do These Yet

### ESP32 Hardware-Dependent Tasks
- **IMU Module**: Needs MPU6050 connected
- **Encoder Module**: Needs encoders connected
- **Motor Driver**: Needs BTS7960 and motors connected
- **Balance Loop Timing**: Needs real hardware to verify 100Hz
- **PID Tuning**: Needs real robot to tune
- **IMU Calibration**: Needs robot on level surface

### Integration Tasks
- End-to-end command flow testing
- Balance stability testing
- Motion command execution
- Serial communication with real ESP32

---

## Recommended Work Order (Before Hardware Arrives)

### Day 1 (If you have 4-6 hours)
1. ✅ Set up development environment (dependencies, tools)
2. ✅ Implement command parser (fully testable)
3. ✅ Implement command queue manager (fully testable)
4. ✅ Set up test infrastructure with mocks

### Day 2 (If you have 4-6 hours)
5. ✅ Implement command handler JSON parsing (ESP32)
6. ✅ Implement balance controller PID algorithm (ESP32)
7. ✅ Implement serial interface (Pi) - test with mocks
8. ✅ Test audio pipeline with any USB mic or files

### Day 3 (If you have 2-3 hours)
9. ✅ Implement main controller structure
10. ✅ Write comprehensive unit tests
11. ✅ Test all modules independently

---

## Testing Without Hardware

### Serial Communication
```python
# Mock serial port for testing
from unittest.mock import Mock, patch

def test_serial_send():
    mock_serial = Mock()
    # Test command sending logic
```

### Balance Controller
```cpp
// Test PID with mock data
float test_angle = 5.0;
float test_velocity = 2.0;
balanceController.update(test_angle, test_velocity);
// Verify output is reasonable
```

### Command Parser
```python
# Test with text inputs
parser = CommandParser()
commands = parser.parse("move forward at speed 0.5")
assert commands[0].command_type == CommandType.MOVE_FORWARD
```

### Audio (with any USB mic)
```python
# Works with any USB microphone
mic = MicrophoneInterface()
mic.start()
audio = mic.capture_audio(duration=3.0)
# Test transcription
```

---

## What You'll Need When Hardware Arrives

### Quick Integration Checklist
- [ ] Connect IMU (I2C)
- [ ] Connect encoders (GPIO interrupts)
- [ ] Connect motors (PWM + enable pins)
- [ ] Verify pin assignments match config.h
- [ ] Calibrate IMU on level surface
- [ ] Test motor directions
- [ ] Tune PID parameters
- [ ] Test balance loop timing (100Hz)

### Critical Hardware Tasks (2-3 hours when hardware arrives)
1. **IMU Calibration** (15 min)
2. **Motor Direction Verification** (15 min)
3. **Encoder Calibration** (30 min)
4. **PID Tuning** (1-2 hours) - This is the time-consuming part
5. **Balance Loop Timing Verification** (15 min)

---

## Time Savings

**If you complete pre-hardware work**: ~12-15 hours of development done
**When hardware arrives**: Only 2-3 hours of integration/tuning needed

**Total time saved**: ~10-12 hours during hackathon

---

## My Recommendation

**YES, definitely do the pre-hardware work!** Here's why:

1. **Command Parser** - 100% doable now, saves 2-3 hours
2. **Command Queue** - 100% doable now, saves 1-2 hours
3. **JSON Parsing** - 100% doable now, saves 2-3 hours
4. **PID Algorithm** - 100% doable now, saves 2-3 hours
5. **Test Infrastructure** - 100% doable now, enables all other testing

**Total**: ~10-12 hours of work you can do NOW that will save time during the hackathon.

The only things that truly need hardware are:
- IMU calibration and reading
- Encoder reading
- Motor control
- PID tuning (needs real robot)
- Balance loop timing verification

Everything else can be implemented and tested with mocks!

---

## Quick Start Commands

### Set Up Development Environment
```bash
# Python side
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# ESP32 side
cd esp32
pio lib install
```

### Run Tests (as you implement)
```bash
# Python tests
pytest tests/pi/ -v

# ESP32 tests (when ready)
cd esp32
pio test
```

### Test Audio (with any USB mic)
```bash
# List audio devices
python -c "import pyaudio; p = pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count())]"
```

---

## Summary

**Do NOW** (before hardware):
- ✅ Command parser (fully testable)
- ✅ Command queue (fully testable)
- ✅ JSON parsing (fully testable)
- ✅ PID algorithm (testable with mock data)
- ✅ Serial interface logic (testable with mocks)
- ✅ Test infrastructure
- ✅ Audio pipeline (works with any USB mic)

**Wait for hardware**:
- ❌ IMU reading/calibration
- ❌ Encoder reading
- ❌ Motor control
- ❌ PID tuning
- ❌ Balance loop timing verification

**Bottom line**: You can do ~70% of the work now and save significant time during the hackathon!
