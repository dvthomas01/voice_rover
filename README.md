# Voice Rover

A voice-controlled self-balancing robot built on a two-tier architecture combining Raspberry Pi for natural language processing and ESP32 for real-time balance control. The system accepts spoken commands through a wake word interface, processes them using Whisper speech-to-text, and executes movement commands while maintaining balance.

## System Architecture

Voice Rover uses a distributed architecture to separate high-level cognitive tasks from low-level control:

**Raspberry Pi Tier**
- Audio capture and wake word detection
- Speech-to-text transcription using OpenAI Whisper
- Natural language command parsing
- Command queue management
- USB serial communication to ESP32

**ESP32 Tier**
- Real-time PID-based balance control
- Motor driver management
- IMU sensor processing
- Command execution
- Safety fail-safes

The two tiers communicate via USB serial using a newline-delimited JSON protocol. This separation allows the computationally intensive speech processing to run on the Pi without interfering with the time-critical balance control loop running on the ESP32.

## Hardware Requirements

### Core Components
- **Raspberry Pi 4** (2GB+ RAM recommended)
- **ESP32 development board** (ESP32-DevKitC or similar)
- **USB microphone** or I2S MEMS microphone
- **IMU sensor** (MPU6050 or MPU9250)
- **Motor drivers** (L298N, DRV8833, or similar H-bridge)
- **DC motors** (2x, with encoders recommended)
- **Self-balancing chassis** (two-wheeled design)

### Power Requirements
- 7.4V-12V LiPo battery for motors (2S-3S)
- 5V power supply for Raspberry Pi (separate or buck converter)
- 3.3V for ESP32 (typically from USB or onboard regulator)

### Connections
- USB cable: Raspberry Pi to ESP32 (data + power)
- I2C: ESP32 to IMU (SDA/SCL)
- PWM + GPIO: ESP32 to motor drivers
- Audio: USB microphone to Raspberry Pi

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

4. Configure serial port in `pi/config.py` (default: `/dev/ttyUSB0`)

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
- "Move forward 2 meters"
- "Turn left 90 degrees"
- "Move backward 1 meter"
- "Turn right 45 degrees"
- "Stop"

**Intermediate Commands:**
- "Turn around" → Expands to: turn 180 degrees
- "Make a circle" → Expands to: series of forward + turn commands
- "Draw a square" → Expands to: forward + turn sequence

**STOP Command:**
The STOP command has the highest priority. It immediately clears the command queue and stops all motors. This command bypasses the normal queue and is sent directly to the ESP32.

## Command Reference

### Primitive Commands

| Command | Parameters | Description |
|---------|------------|-------------|
| `move_forward` | `distance` (meters), `speed` (optional) | Move forward |
| `move_backward` | `distance` (meters), `speed` (optional) | Move backward |
| `turn_left` | `angle` (degrees) | Rotate left |
| `turn_right` | `angle` (degrees) | Rotate right |
| `stop` | None | Immediate stop |

### Intermediate Commands

Intermediate commands are expanded by the command parser into sequences of primitive commands:

- **turn_around**: `turn_left(180)`
- **circle**: Configurable radius, expanded to forward + turn sequence
- **square**: Configurable size, expanded to 4x (forward + turn_right(90))

## Communication Protocol

Commands are sent from Raspberry Pi to ESP32 as newline-delimited JSON:

```json
{"command": "move_forward", "parameters": {"distance": 2.0, "speed": 0.5}, "priority": 0}
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
│   │   ├── balance/       # PID balance controller
│   │   ├── motor_control/ # Motor drivers
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

### Modifying Balance Parameters

Edit `esp32/include/config.h`:
- `KP`, `KI`, `KD`: PID gains
- `BALANCE_ANGLE_OFFSET`: Target angle for balance
- `BALANCE_LOOP_FREQ`: Control loop frequency (Hz)

Tune parameters iteratively. Start with KP, then add KD, finally KI.

### Testing Individual Modules

Python modules can be tested independently:
```bash
pytest tests/pi/test_command_parser.py
```

ESP32 firmware can be tested with serial loopback or mock serial port.

## Safety Features

- **STOP command priority**: STOP always clears the queue and executes immediately
- **Balance fail-safe**: ESP32 monitors tilt angle; motors stop if angle exceeds safe threshold
- **Serial timeout**: If serial connection lost, ESP32 enters safe mode
- **Command validation**: All JSON commands validated before execution

## Troubleshooting

### Wake word not detected
- Check microphone connection and permissions
- Verify `WAKE_WORD_SENSITIVITY` in `pi/config.py`
- Test microphone: `arecord -d 5 test.wav`

### Commands not executing
- Check serial connection: `ls /dev/ttyUSB*`
- Monitor ESP32 serial output: `pio device monitor`
- Verify ESP32 firmware uploaded successfully

### Robot not balancing
- Calibrate IMU sensor
- Tune PID parameters in `esp32/include/config.h`
- Check motor connections and directions
- Verify IMU orientation matches code expectations

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
- PID balance controller
- Motor control implementation
- IMU sensor integration

The architecture and interfaces are stable. Development can proceed in parallel on Pi and ESP32 codebases.

## License

[Specify license here]

## Contributing

[Specify contribution guidelines here]
