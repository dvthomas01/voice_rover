# Hackathon Setup Guide

## Quick Start (2.5 Day Hackathon)

This guide helps you get started quickly for parallel development.

---

## Repository Structure

### ESP32 Side (Hardware Control)
```
esp32/
├── src/
│   ├── sensors/
│   │   ├── imu.h/cpp          # MPU6050 IMU interface [TODO]
│   │   └── encoder_reader.h/cpp  # Encoder reading [TODO]
│   ├── balance/
│   │   └── balance_controller.h/cpp  # PID balance control [TODO]
│   ├── motor_control/
│   │   └── motor_driver.h/cpp  # BTS7960 motor driver [TODO]
│   ├── command_handler/
│   │   └── command_handler.h/cpp  # Command execution [TODO]
│   └── main.cpp              # Main loop [TODO: Integrate all modules]
├── include/
│   └── config.h              # ✅ Complete - All pins and parameters defined
└── platformio.ini            # ✅ Complete - All dependencies listed
```

### Raspberry Pi Side (Voice Processing)
```
pi/
├── audio_input/
│   └── microphone.py         # Audio capture [TODO]
├── wake_word/
│   └── detector.py           # Porcupine wake word [TODO]
├── whisper/
│   └── transcriber.py        # Whisper STT [TODO]
├── command_parser/
│   ├── command_schema.py     # ✅ Complete - All command types defined
│   └── parser.py             # NLP to commands [TODO]
├── command_queue/
│   └── queue_manager.py      # Thread-safe queue [TODO]
├── serial_comm/
│   └── serial_interface.py   # ESP32 communication [TODO]
├── main_controller.py        # Main orchestration [TODO]
└── config.py                 # ✅ Complete - All settings defined
```

---

## Parallel Development Paths

### Path 1: ESP32 Hardware Control (Team Member 1-2)
**Focus**: Balance control, motor control, sensor reading

**Tasks**:
1. **IMU Module** (`esp32/src/sensors/imu.cpp`)
   - Initialize MPU6050
   - Read accelerometer/gyroscope
   - Implement complementary filter for pitch angle
   - Calibration routine

2. **Encoder Module** (`esp32/src/sensors/encoder_reader.cpp`)
   - Setup interrupt handlers
   - Implement quadrature decoding
   - Calculate velocity

3. **Balance Controller** (`esp32/src/balance/balance_controller.cpp`)
   - Implement PID algorithm
   - Add motion setpoint integration
   - Tune PID parameters (KP, KI, KD)

4. **Motor Driver** (`esp32/src/motor_control/motor_driver.cpp`)
   - Implement BTS7960 control (PWM + enable pins)
   - Test motor direction and speed

5. **Command Handler** (`esp32/src/command_handler/command_handler.cpp`)
   - Parse JSON commands
   - Execute primitive commands (modify balance setpoints)
   - Implement command queue

6. **Main Loop** (`esp32/src/main.cpp`)
   - Integrate all modules
   - 100Hz balance loop
   - Command processing

**Testing**: Use serial monitor to send test commands, verify balance

---

### Path 2: Raspberry Pi Voice Pipeline (Team Member 3-4)
**Focus**: Audio capture, wake word, STT, command parsing

**Tasks**:
1. **Microphone** (`pi/audio_input/microphone.py`)
   - Initialize PyAudio
   - Capture from Samson Go Mic USB
   - Resample 44.1kHz/48kHz -> 16kHz for Whisper

2. **Wake Word** (`pi/wake_word/detector.py`)
   - Initialize Porcupine
   - Get access key from Picovoice
   - Test wake word detection

3. **Whisper** (`pi/whisper/transcriber.py`)
   - Load Whisper model (start with "base" for speed)
   - Transcribe audio to text
   - Handle audio format conversion

4. **Command Parser** (`pi/command_parser/parser.py`)
   - Pattern matching for commands
   - Extract parameters (speed, angle, duration)
   - Expand intermediate commands to primitives

5. **Command Queue** (`pi/command_queue/queue_manager.py`)
   - Thread-safe PriorityQueue
   - Handle STOP command priority

6. **Serial Interface** (`pi/serial_comm/serial_interface.py`)
   - Connect to ESP32
   - Send JSON commands
   - Read responses

7. **Main Controller** (`pi/main_controller.py`)
   - Multi-threaded architecture
   - Wake word listener thread
   - Command executor thread
   - Serial communicator thread

**Testing**: Test each module independently, mock ESP32 for testing

---

## Dependencies Setup

### ESP32 (PlatformIO)
```bash
cd esp32
pio lib install  # Installs all dependencies from platformio.ini
```

**Dependencies** (already in `platformio.ini`):
- Adafruit MPU6050 library
- ArduinoJson
- Wire (I2C, built-in)

### Raspberry Pi
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Dependencies** (already in `requirements.txt`):
- pyserial (ESP32 communication)
- numpy, pyaudio (audio processing)
- scipy (audio resampling)
- pvporcupine (wake word - needs API key)
- openai-whisper, torch (speech-to-text)
- pytest (testing)

**Porcupine Access Key**:
1. Sign up at https://console.picovoice.ai/
2. Get free access key
3. Set environment variable: `export PORCUPINE_ACCESS_KEY="your_key_here"`

---

## Integration Points

### ESP32 → Pi
- **Serial Communication**: JSON commands over USB serial (115200 baud)
- **Command Format**: `{"command": "move_forward", "parameters": {"speed": 0.4}, "priority": 0}`
- **Response Format**: `{"success": true, "message": "Command executed"}`

### Pi → ESP32
- **Wake Word** → **Audio Capture** → **Whisper STT** → **Parser** → **Queue** → **Serial** → **ESP32**
- **STOP Command**: Bypasses queue, sent immediately

### Balance Control
- **Balance Loop**: Runs continuously at 100Hz (never disabled)
- **Motion Commands**: Modify balance controller setpoints (don't replace control)
- **STOP Command**: Clears setpoints, returns to neutral balance

---

## Testing Strategy

### Without Hardware
- **ESP32**: Use serial loopback (connect TX to RX)
- **Pi**: Mock serial interface, test command parsing
- **Audio**: Use pre-recorded audio files for testing

### With Hardware
- **ESP32**: Test balance control first (most critical)
- **Pi**: Test voice pipeline independently
- **Integration**: Test end-to-end with real hardware

---

## Critical TODOs

### ESP32
- [ ] IMU calibration routine
- [ ] PID tuning (start with KP only)
- [ ] Motor direction verification
- [ ] Encoder calibration
- [ ] Balance loop timing (must be 100Hz)

### Pi
- [ ] Porcupine access key setup
- [ ] Whisper model download (happens automatically)
- [ ] Audio device selection (Samson Go Mic)
- [ ] Serial port detection
- [ ] Command pattern matching

---

## Time Estimates (2.5 Days)

### Day 1 Morning
- ESP32: IMU + Encoder modules (2-3 hours)
- Pi: Microphone + Wake word (2-3 hours)

### Day 1 Afternoon
- ESP32: Balance controller PID (3-4 hours)
- Pi: Whisper + Parser (3-4 hours)

### Day 2 Morning
- ESP32: Motor driver + Command handler (3-4 hours)
- Pi: Queue + Serial + Main controller (3-4 hours)

### Day 2 Afternoon
- Integration testing (2-3 hours)
- PID tuning (2-3 hours)
- Bug fixes

### Day 3 (Half Day)
- Final testing
- Demo preparation
- Documentation

---

## Quick Reference

### ESP32 Pin Assignments (from `config.h`)
- **Motors**: PWM 25/32, R_EN 26/33, L_EN 27/34
- **Encoders**: Left A/B 18/19, Right A/B 16/17
- **IMU**: I2C SDA 21, SCL 22

### Command Types
- **Primitive**: move_forward, move_backward, rotate_clockwise, rotate_counterclockwise, stop
- **Intermediate**: turn_left, turn_right, move_forward_for_time, make_square, etc.
- **Advanced**: dance

### Balance Parameters (from `config.h`)
- **PID**: KP=40.0, KI=0.5, KD=2.0 (tune these!)
- **Loop Frequency**: 100Hz (10ms period)
- **Max Tilt**: 45° (fall detection)

---

## Getting Help

- **ESP32 Issues**: Check serial monitor output, verify pin connections
- **Pi Issues**: Check logs, verify dependencies installed
- **Balance Issues**: Start with KP only, add KD, finally KI
- **Audio Issues**: Check microphone permissions, verify device selection

---

## Success Criteria

- [ ] Robot maintains balance for > 30 seconds
- [ ] Wake word detection works reliably
- [ ] Commands execute correctly
- [ ] STOP command responds in < 100ms
- [ ] Balance maintained during motion

Good luck! 🚀
