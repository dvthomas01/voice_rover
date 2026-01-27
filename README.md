# Voice Rover

A voice-controlled self-balancing inverted pendulum robot built on a two-tier architecture combining Raspberry Pi for natural language processing and ESP32 for real-time balance control. The system accepts spoken commands through a wake word interface, processes them using Whisper speech-to-text, and executes movement commands while continuously maintaining balance using an onboard IMU and motor encoders.

## System Architecture

Voice Rover uses a distributed architecture to separate high-level cognitive tasks from low-level control:

**Raspberry Pi Tier**
- Audio capture and wake word detection
- Speech-to-text transcription using OpenAI Whisper
- Natural language command parsing
- Command queue management
- USB serial communication to ESP32

**ESP32 Tier**
- Real-time PID-based balance control (100Hz loop)
- IMU sensor processing (MPU6050)
- Motor driver management (BTS7960)
- Encoder reading and feedback
- Command execution
- Safety fail-safes

The two tiers communicate via USB serial using a newline-delimited JSON protocol. This separation allows the computationally intensive speech processing to run on the Pi without interfering with the time-critical balance control loop running on the ESP32.

## Hardware Requirements

### Core Components
- **Raspberry Pi 4** (2GB or more)
- **ESP32 development board** (ESP32-DevKitC or similar)
- **USB microphone** (Samson Go Mic USB confirmed)
- **IMU sensor** (MPU6050) - Required for balance control
- **Motor driver** (BTS7960)
- **DC motors with encoders** (Dagu RS034 Motor and Encoder Kit confirmed)
- **Self-balancing chassis** (two-wheeled inverted pendulum)

### Power Requirements
- 2-cell LiPo battery (7.4V) for motors and logic power
- Buck converter for stepping down battery voltage to logic levels
- 5V power supply for Raspberry Pi (separate or from buck converter)
- 3.3V for ESP32 (typically from USB or onboard regulator)

### Connections
- **USB serial**: Raspberry Pi to ESP32 (data + power)
- **I2C**: ESP32 to IMU (SDA/SCL) - Required for balance control
- **PWM and GPIO**: ESP32 to motor drivers (BTS7960)
- **Encoder signals**: Motors to ESP32
- **Audio**: USB microphone to Raspberry Pi
- **Power**: 2-cell LiPo battery to motor driver and regulators

## Software Requirements

### Raspberry Pi
- Raspberry Pi OS (64-bit recommended)
- Python 3.8 or higher
- System packages: `portaudio19-dev`, `python3-pyaudio`

### ESP32
- PlatformIO Core or PlatformIO IDE
- Arduino framework for ESP32

## Installation

### Raspberry Pi Setup

1. Install system dependencies:
```bash
sudo apt update
sudo apt install portaudio19-dev python3-pip python3-venv git
```

2. Clone repository:
```bash
git clone <repository-url>
cd voice_rover
```

3. Create virtual environment and install Python dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. Set Porcupine access key (for wake word detection):
```bash
export PORCUPINE_ACCESS_KEY="your-key-here"
# Or add to ~/.zshrc or ~/.bashrc for persistence
```
Get a free key from: https://console.picovoice.ai/

5. Configure serial port in `pi/config.py` (default: `/dev/ttyUSB0`)

### ESP32 Setup

1. Install PlatformIO:
```bash
pip install platformio
```

2. Build and upload firmware:
```bash
cd esp32
pio run -t upload
```

3. Test serial connection:
```bash
pio device monitor
```

### Hardware Connections

Refer to `docs/HARDWARE_SETUP.md` for detailed wiring diagrams and pin assignments.

## Usage

### Starting the System

1. Connect ESP32 to Raspberry Pi via USB
2. Activate Python virtual environment:
```bash
source venv/bin/activate
```
3. Run the main controller:
```bash
python pi/main_controller.py
```

### Voice Commands

The system activates on the wake word **"jarvis"** (configurable in `pi/config.py`).

After wake word detection, speak a command clearly. The system will transcribe, parse, and execute it.

### Command Examples

**Primitive Commands:**
- "Move forward" (default speed 0.4)
- "Move backward" (default speed 0.4)
- "Rotate clockwise" (default speed 0.4)
- "Rotate counterclockwise" (default speed 0.4)
- "Stop"

**Intermediate Commands:**
- "Turn left 90 degrees" (default speed 0.4)
- "Turn right 45 degrees" (default speed 0.4)
- "Move forward for 2 seconds" (default speed 0.4)
- "Move backward for 1 second" (default speed 0.4)
- "Make a square" (default side length 0.5m, speed 0.4)
- "Make a circle" (default radius 0.5m, speed 0.4, direction left)
- "Make a star" (default size 0.5m, speed 0.4, optional)
- "Zigzag" (default segment 0.3m, angle 45°, 4 repetitions, speed 0.4)
- "Spin for 2 seconds" (default speed 0.5)

**Advanced Commands:**
- "Dance"

**STOP Command:**
The STOP command has the highest priority. It immediately clears the command queue and stops all motors. This command bypasses the normal queue and is sent directly to the ESP32.

## Command Reference

### Primitive Commands

| Command | Parameters | Description |
|---------|------------|-------------|
| `move_forward` | `speed` (default: 0.4) | Move forward continuously |
| `move_backward` | `speed` (default: 0.4) | Move backward continuously |
| `rotate_clockwise` | `speed` (default: 0.4) | Rotate clockwise continuously |
| `rotate_counterclockwise` | `speed` (default: 0.4) | Rotate counterclockwise continuously |
| `stop` | None | Immediate stop |

### Intermediate Commands

Intermediate commands are expanded by the command parser into sequences of primitive commands:

| Command | Parameters | Description |
|---------|------------|-------------|
| `turn_left` | `angle` (default: 90), `speed` (default: 0.4) | Rotate left by specified angle |
| `turn_right` | `angle` (default: 90), `speed` (default: 0.4) | Rotate right by specified angle |
| `move_forward_for_time` | `duration` (default: 1.0), `speed` (default: 0.4) | Move forward for specified duration |
| `move_backward_for_time` | `duration` (default: 1.0), `speed` (default: 0.4) | Move backward for specified duration |
| `make_square` | `side_length` (default: 0.5), `speed` (default: 0.4) | Draw a square pattern |
| `make_circle` | `radius` (default: 0.5), `speed` (default: 0.4), `direction` (default: "left") | Draw a circular pattern |
| `make_star` | `size` (default: 0.5), `speed` (default: 0.4) | Draw a star pattern (optional) |
| `zigzag` | `segment_length` (default: 0.3), `angle` (default: 45), `repetitions` (default: 4), `speed` (default: 0.4) | Perform zigzag movement pattern |
| `spin` | `duration` (default: 2.0), `speed` (default: 0.5) | Spin in place for specified duration |

### Advanced Commands

| Command | Parameters | Description |
|---------|------------|-------------|
| `dance` | None | Perform dance routine |

## Communication Protocol

Commands are sent from Raspberry Pi to ESP32 as newline-delimited JSON:

```json
{"command": "move_forward", "parameters": {"speed": 0.4}, "priority": 0}
```

ESP32 responds with:

```json
{"success": true, "message": "Command executed"}
```

See `docs/API.md` for complete protocol specification.

## Development Guide

### Repository Structure

```
voice_rover/
├── pi/                    # Raspberry Pi codebase
│   ├── audio_input/       # Microphone interface
│   ├── wake_word/         # Wake word detection
│   ├── whisper/           # Speech-to-text
│   ├── command_parser/    # NLP to structured commands
│   ├── command_queue/     # Thread-safe queue
│   ├── serial_comm/       # USB serial interface
│   ├── main_controller.py # Main orchestration
│   └── config.py          # Configuration
├── esp32/                 # ESP32 firmware
│   ├── src/
│   │   ├── sensors/       # IMU and encoder modules
│   │   ├── balance/       # PID balance controller
│   │   ├── motor_control/ # Motor driver control (BTS7960)
│   │   └── command_handler/ # Command parser
│   └── include/config.h   # ESP32 configuration
├── tests/                 # Test suites
├── docs/                  # Documentation
└── scripts/               # Utility scripts
```

### Adding New Commands

1. **Define command in schema**: Edit `pi/command_parser/command_schema.py`
   - Add new `CommandType` enum value
   - Define parameters

2. **Add parsing logic**: Edit `pi/command_parser/parser.py`
   - Add pattern matching for voice command
   - Map to `Command` object

3. **Implement on ESP32**: Edit `esp32/src/command_handler/command_handler.cpp`
   - Add case in `executeMovementCommand()`
   - Implement motor control logic

### Modifying Motor Control Parameters

Edit `esp32/include/config.h`:
- Motor PWM pins and direction pins
- Encoder pins
- Speed limits and acceleration parameters

Adjust motor speeds and encoder calibration as needed for your chassis.

### Testing Individual Modules

Python modules can be tested independently:
```bash
pytest tests/pi/test_command_parser.py
```

ESP32 firmware can be tested with serial loopback or mock serial port.

## Safety Features

- **STOP command priority**: STOP always clears the queue and executes immediately
- **Balance loop continuity**: Balance control runs continuously at 100Hz and is never disabled
- **Fall detection**: ESP32 monitors tilt angle; motors stop if angle exceeds safe threshold
- **Serial timeout**: If serial connection lost, ESP32 enters safe mode (returns to neutral balance)
- **Command validation**: All JSON commands validated before execution
- **Motion integration**: Motion commands modify balance setpoints, don't replace balance control

## Troubleshooting

### Wake word not detected
- Check microphone connection and permissions
- Verify `PORCUPINE_ACCESS_KEY` environment variable is set
- Verify `WAKE_WORD_SENSITIVITY` in `pi/config.py`
- Test microphone: `python scripts/test_microphone_input.py`
- Test wake word detection: `python scripts/test_wake_word_detection.py`

### Commands not executing
- Check serial connection: `ls /dev/ttyUSB*`
- Monitor ESP32 serial output: `pio device monitor`
- Verify ESP32 firmware uploaded successfully

### Robot not balancing
- Calibrate IMU sensor on level surface
- Tune PID parameters in `esp32/include/config.h` (start with KP, add KD, finally KI)
- Check motor connections and directions
- Verify IMU orientation matches code expectations
- Check that balance loop is running at 100Hz

### Robot not moving correctly
- Check motor connections and directions
- Verify encoder connections and calibration
- Check motor driver (BTS7960) power and control signals
- Verify encoder pulses are being read correctly
- Ensure motion commands are modifying balance setpoints correctly

### Serial communication errors
- Ensure baud rate matches on both Pi and ESP32 (115200)
- Check USB cable quality (data + power lines)
- Verify user has serial port permissions: `sudo usermod -a -G dialout $USER`

## Project Status

**Current Phase**: Skeleton/Planning

This repository contains a complete modular skeleton with clear interfaces and type signatures. Full implementations of the following components are pending:

- Audio capture and preprocessing
- Wake word detection integration
- Whisper transcription
- Command parsing logic
- PID balance controller implementation
- IMU sensor integration (MPU6050)
- Motor control implementation (BTS7960 driver)
- Encoder reading and feedback
- Command execution on ESP32

The architecture and interfaces are stable. Development can proceed in parallel on Pi and ESP32 codebases.

**Key Architecture Points**:
- Balance control is the PRIMARY function - runs continuously at 100Hz
- Motion commands modify balance controller setpoints (don't replace control)
- IMU (MPU6050) is required for pitch angle estimation
- Balance loop is never disabled during operation (safety critical)

## License

[Specify license here]

## Contributing

[Specify contribution guidelines here]
