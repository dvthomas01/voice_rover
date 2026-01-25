# Implementation Plan: Repository Revamp for Self-Balancing Architecture

## Executive Summary

The repository currently describes a **differential drive robot** but needs to be revamped to match the **self-balancing inverted pendulum** architecture. This plan outlines all changes needed to align the codebase with the intended functionality.

---

## Critical Misalignments Identified

### 1. Project Description (HIGH PRIORITY)
- **Current**: README describes "differential drive robot" with "static, non-balancing chassis"
- **Required**: Self-balancing inverted pendulum robot
- **Impact**: Fundamental misunderstanding of project

### 2. Hardware Components (HIGH PRIORITY)
- **Current**: README says "does not require balance control or IMU sensors"
- **Required**: MPU6050 IMU is core component, balance control is primary function
- **Impact**: Missing critical hardware specifications

### 3. ESP32 Configuration (HIGH PRIORITY)
- **Current**: `config.h` missing IMU I2C pins, PID parameters, balance loop frequency
- **Required**: Complete balance control configuration
- **Impact**: Code won't compile, balance controller can't function

### 4. Command Schema (MEDIUM PRIORITY)
- **Current**: Old command types (TURN_LEFT, TURN_RIGHT, TURN_AROUND, CIRCLE, SQUARE)
- **Required**: New command set (rotate_clockwise, rotate_counterclockwise, move_forward_for_time, etc.)
- **Impact**: Commands don't match intended functionality

### 5. API Documentation (MEDIUM PRIORITY)
- **Current**: Distance-based commands in API.md
- **Required**: Time/speed-based commands
- **Impact**: Documentation doesn't match implementation requirements

### 6. Missing Modules (HIGH PRIORITY)
- **Current**: No encoder reader module, no IMU module
- **Required**: Both modules needed for balance control
- **Impact**: Balance controller can't function without sensor inputs

### 7. Motor Driver Interface (MEDIUM PRIORITY)
- **Current**: Config has single DIR pin, but motor_driver.h expects dir1/dir2
- **Required**: Align with BTS7960 (two direction pins per motor: R_EN, L_EN)
- **Impact**: Motor control won't work correctly

### 8. Balance Controller Integration (HIGH PRIORITY)
- **Current**: Balance controller exists but motion commands don't integrate with it
- **Required**: Motion commands modify balance controller setpoints
- **Impact**: Robot can't execute motion while balancing

---

## Implementation Plan

### Phase 1: Core Architecture Corrections

#### 1.1 Update Project Documentation
**Files**: `README.md`, `docs/API.md`

**Changes**:
- Change project description from "differential drive" to "self-balancing inverted pendulum"
- Restore IMU (MPU6050) as core component
- Update hardware list to reflect self-balancing chassis
- Update connections to include I2C for IMU
- Update API.md to remove distance-based commands, add time/speed-based commands
- Update troubleshooting section (remove "robot not balancing" → update to balance tuning)

**Estimated Time**: 1-2 hours

#### 1.2 Fix ESP32 Configuration
**File**: `esp32/include/config.h`

**Changes**:
- Add IMU I2C pins: `I2C_SDA`, `I2C_SCL`
- Add PID parameters: `KP`, `KI`, `KD`
- Add balance loop frequency: `BALANCE_LOOP_FREQ` (100 Hz)
- Add balance angle offset: `BALANCE_ANGLE_OFFSET`
- Fix motor driver pins: Use two direction pins per motor (R_EN, L_EN for BTS7960)
- Add encoder pin definitions (already present, verify)
- Add safety parameters: `MAX_TILT_ANGLE`, `FALL_DETECTION_THRESHOLD`

**Estimated Time**: 30 minutes

#### 1.3 Update Command Schema
**File**: `pi/command_parser/command_schema.py`

**Changes**:
- Remove old commands: `TURN_LEFT`, `TURN_RIGHT`, `TURN_AROUND`, `CIRCLE`, `SQUARE`
- Add primitive commands:
  - `MOVE_FORWARD` (speed parameter)
  - `MOVE_BACKWARD` (speed parameter)
  - `ROTATE_CLOCKWISE` (speed parameter)
  - `ROTATE_COUNTERCLOCKWISE` (speed parameter)
  - `STOP` (no parameters)
- Add intermediate commands:
  - `TURN_LEFT` (angle, speed)
  - `TURN_RIGHT` (angle, speed)
  - `MOVE_FORWARD_FOR_TIME` (duration, speed)
  - `MOVE_BACKWARD_FOR_TIME` (duration, speed)
  - `MAKE_SQUARE` (side_length, speed)
  - `MAKE_CIRCLE` (radius, speed, direction)
  - `MAKE_STAR` (size, speed) - optional
  - `ZIGZAG` (segment_length, angle, repetitions, speed)
  - `SPIN` (duration, speed)
- Add advanced command:
  - `DANCE` (no parameters)

**Estimated Time**: 1 hour

---

### Phase 2: ESP32 Core Modules

#### 2.1 Create IMU Module
**New Files**: `esp32/src/sensors/imu.h`, `esp32/src/sensors/imu.cpp`

**Functionality**:
- Initialize MPU6050 over I2C
- Read accelerometer and gyroscope data
- Calculate pitch angle (complementary filter or Kalman filter)
- Calculate angular velocity
- Handle sensor errors and calibration
- Provide angle and angular velocity to balance controller

**Interface**:
```cpp
class IMU {
    bool begin();
    bool update();  // Read sensor, update angle estimate
    float getPitchAngle();  // Degrees
    float getAngularVelocity();  // Degrees/second
    bool isCalibrated();
    void calibrate();  // Calibrate on level surface
};
```

**Dependencies**: Adafruit MPU6050 library (already in platformio.ini)

**Estimated Time**: 3-4 hours

#### 2.2 Create Encoder Reader Module
**New Files**: `esp32/src/sensors/encoder_reader.h`, `esp32/src/sensors/encoder_reader.cpp`

**Functionality**:
- Read quadrature encoder pulses (Dagu RS034)
- Count pulses with interrupts
- Calculate wheel velocity
- Calculate wheel position
- Support both left and right encoders
- Handle encoder direction detection

**Interface**:
```cpp
class EncoderReader {
    void begin(int pinA, int pinB);
    long getPosition();  // Total pulses
    float getVelocity();  // Pulses per second
    void reset();
    static void interruptHandler();  // Static for ISR
};
```

**Dependencies**: Standard Encoder library or custom interrupt-based counting

**Estimated Time**: 2-3 hours

#### 2.3 Update Motor Driver for BTS7960
**Files**: `esp32/src/motor_control/motor_driver.h`, `esp32/src/motor_control/motor_driver.cpp`

**Changes**:
- Update constructor to match BTS7960: `MotorDriver(int pwm_pin, int r_en_pin, int l_en_pin)`
- Implement proper BTS7960 control:
  - Forward: R_EN = HIGH, L_EN = LOW, PWM = speed
  - Reverse: R_EN = LOW, L_EN = HIGH, PWM = speed
  - Stop: R_EN = LOW, L_EN = LOW, PWM = 0
- Update `setSpeed()` to handle direction via enable pins
- Add PWM frequency configuration (BTS7960 typically 20kHz)

**Estimated Time**: 1-2 hours

#### 2.4 Implement Balance Controller
**Files**: `esp32/src/balance/balance_controller.cpp`, `esp32/src/balance/balance_controller.h`

**Changes**:
- Implement PID control algorithm
- Add encoder velocity feedback (optional velocity feedforward)
- Implement integral windup protection
- Add fall detection (angle limits)
- Add setpoint modification methods for motion commands:
  - `setVelocitySetpoint(float velocity)` - for forward/backward motion
  - `setRotationSetpoint(float angular_velocity)` - for rotation
  - `setNeutral()` - return to balance-only mode
- Ensure balance loop never stops (safety critical)

**Estimated Time**: 4-5 hours

#### 2.5 Update ESP32 Main Loop
**File**: `esp32/src/main.cpp`

**Changes**:
- Remove incorrect balance controller initialization (fix undefined constants)
- Initialize IMU module
- Initialize encoder readers
- Fix balance loop to use actual IMU data
- Integrate encoder velocity into balance controller
- Ensure balance loop runs at fixed 100Hz frequency
- Add command queue processing (non-blocking)
- Implement motion command execution that modifies balance setpoints

**Estimated Time**: 2-3 hours

#### 2.6 Implement Command Handler
**Files**: `esp32/src/command_handler/command_handler.cpp`, `esp32/src/command_handler/command_handler.h`

**Changes**:
- Implement JSON parsing with ArduinoJson
- Add command validation (type, parameters, ranges)
- Implement primitive command execution:
  - `move_forward`: Set velocity setpoint on balance controller
  - `move_backward`: Set negative velocity setpoint
  - `rotate_clockwise`: Set rotation setpoint
  - `rotate_counterclockwise`: Set negative rotation setpoint
  - `stop`: Clear setpoints, return to neutral balance
- Implement intermediate command execution:
  - Time-based commands: Track duration, clear setpoint when complete
  - Angle-based commands: Use encoder feedback to achieve target angle
  - Pattern commands: Execute sequence of primitives
- Implement command queue (FIFO)
- STOP command clears queue and immediately returns to neutral
- Send response messages back to Pi

**Estimated Time**: 5-6 hours

---

### Phase 3: Raspberry Pi Modules

#### 3.1 Update Command Parser
**File**: `pi/command_parser/parser.py`

**Changes**:
- Implement natural language pattern matching
- Parse primitive commands:
  - "move forward" → `move_forward(speed=0.4)`
  - "move backward" → `move_backward(speed=0.4)`
  - "rotate clockwise" → `rotate_clockwise(speed=0.4)`
  - "rotate counterclockwise" → `rotate_counterclockwise(speed=0.4)`
  - "stop" → `stop()`
- Parse intermediate commands:
  - "turn left 90 degrees" → `turn_left(angle=90, speed=0.4)`
  - "turn right 45 degrees" → `turn_right(angle=45, speed=0.4)`
  - "move forward for 2 seconds" → `move_forward_for_time(duration=2.0, speed=0.4)`
  - "move backward for 1 second" → `move_backward_for_time(duration=1.0, speed=0.4)`
  - "make a square" → Expand to sequence of `move_forward_for_time` + `turn_right`
  - "make a circle" → Expand to sequence of forward + turn commands
  - "make a star" → Expand to star pattern (optional)
  - "zigzag" → Expand to zigzag pattern
  - "spin for 2 seconds" → `spin(duration=2.0, speed=0.5)`
- Parse advanced commands:
  - "dance" → Expand to dance routine sequence
- Handle parameter extraction (speed, angle, duration, etc.)
- Return list of Command objects (intermediate commands expand to primitives)

**Estimated Time**: 4-5 hours

#### 3.2 Implement Command Queue Manager
**File**: `pi/command_queue/queue_manager.py`

**Changes**:
- Implement thread-safe PriorityQueue
- Implement `enqueue()` with priority handling
- Implement `dequeue()` with timeout
- Implement `clear()` for STOP command (must be thread-safe)
- Implement `is_empty()` and `size()` helpers
- Ensure STOP command (priority=100) always dequeues first

**Estimated Time**: 2 hours

#### 3.3 Implement Serial Interface
**File**: `pi/serial_comm/serial_interface.py`

**Changes**:
- Implement USB serial connection
- Implement JSON serialization/deserialization
- Implement reconnection logic with exponential backoff
- Implement timeout handling
- Implement STOP command bypass (send immediately, don't queue)
- Handle response messages from ESP32
- Thread-safe read/write operations

**Estimated Time**: 3-4 hours

#### 3.4 Implement Audio Pipeline
**Files**: `pi/audio_input/microphone.py`, `pi/wake_word/detector.py`, `pi/whisper/transcriber.py`

**Changes**:
- **Microphone**: Capture audio from Samson Go Mic USB (44.1kHz/48kHz, resample to 16kHz for Whisper)
- **Wake Word**: Integrate Porcupine for "jarvis" detection
- **Whisper**: Load model, transcribe audio to text
- Handle audio device connection/disconnection
- Buffer management for low latency

**Estimated Time**: 4-5 hours

#### 3.5 Implement Main Controller
**File**: `pi/main_controller.py`

**Changes**:
- Implement multi-threaded architecture:
  - Thread 1: Wake word listener (continuous)
  - Thread 2: Command executor (processes queue)
  - Thread 3: Serial communicator (sends commands, receives responses)
- Implement wake word → audio capture → STT → parser → queue flow
- Implement command executor loop (dequeue and send to ESP32)
- Implement STOP command handling (bypass queue, send immediately)
- Implement graceful shutdown
- Error handling and recovery

**Estimated Time**: 3-4 hours

---

### Phase 4: Integration and Testing

#### 4.1 Update Documentation
**Files**: `docs/HARDWARE_SETUP.md`, `docs/API.md`

**Changes**:
- Update hardware setup for self-balancing chassis
- Add IMU calibration procedure
- Update wiring diagrams (add I2C for IMU)
- Update API.md with correct command set
- Add balance tuning guide
- Add troubleshooting for balance issues

**Estimated Time**: 2-3 hours

#### 4.2 Create Test Infrastructure
**Files**: Test files in `tests/pi/`, `tests/esp32/`

**Changes**:
- Unit tests for command parser (various phrasings)
- Unit tests for command queue (priority, thread safety)
- Unit tests for serial interface (with mocks)
- ESP32 tests with serial loopback
- Mock hardware for testing without physical components

**Estimated Time**: 3-4 hours

#### 4.3 Integration Testing
**Activities**:
- Test serial communication (Pi ↔ ESP32)
- Test command flow end-to-end
- Test STOP command priority
- Test balance during motion commands
- Hardware-in-the-loop testing

**Estimated Time**: 4-6 hours

---

## Implementation Order

### Week 1: Foundation
1. **Day 1-2**: Phase 1 (Documentation and Configuration)
   - Update README and API docs
   - Fix ESP32 config.h
   - Update command schema

2. **Day 3-5**: Phase 2.1-2.3 (ESP32 Sensors and Motor Driver)
   - Create IMU module
   - Create encoder reader module
   - Update motor driver for BTS7960

### Week 2: Core Control
3. **Day 1-3**: Phase 2.4-2.6 (ESP32 Control)
   - Implement balance controller
   - Update main loop
   - Implement command handler

4. **Day 4-5**: Phase 3.1-3.2 (Pi Command Processing)
   - Update command parser
   - Implement command queue manager

### Week 3: Integration
5. **Day 1-3**: Phase 3.3-3.5 (Pi Audio Pipeline)
   - Implement serial interface
   - Implement audio pipeline
   - Implement main controller

6. **Day 4-5**: Phase 4 (Testing and Documentation)
   - Update hardware docs
   - Create tests
   - Integration testing

---

## Risk Mitigation

### High Risk Areas
1. **Balance Controller Tuning**: May require significant iteration
   - Mitigation: Start with known PID values, test incrementally
   - Plan for extended tuning phase

2. **IMU Calibration**: Critical for accurate balance
   - Mitigation: Implement automatic calibration routine
   - Test on level surface before operation

3. **Real-Time Performance**: Balance loop must run at 100Hz
   - Mitigation: Profile code, optimize critical paths
   - Use hardware timers for precise timing

4. **Command Integration**: Motion commands must not disrupt balance
   - Mitigation: Motion modifies setpoints, doesn't replace control
   - Test each command type individually

### Medium Risk Areas
1. **Serial Communication Latency**: May affect command responsiveness
   - Mitigation: Use appropriate buffer sizes, test with real hardware

2. **Encoder Resolution**: High-res mode may overload interrupts
   - Mitigation: Use hardware pulse counter if available, or optimize ISR

3. **Audio Processing Latency**: May delay command execution
   - Mitigation: Optimize Whisper model size, use efficient audio processing

---

## Success Criteria

- [ ] Robot maintains balance autonomously for > 30 seconds
- [ ] All primitive commands execute correctly
- [ ] All intermediate commands execute correctly
- [ ] STOP command responds in < 100ms
- [ ] Balance maintained during motion commands
- [ ] Wake word detection accuracy > 90%
- [ ] Command recognition accuracy > 85%
- [ ] System handles errors gracefully

---

## Notes

- Balance controller code already exists in repository (good starting point)
- MPU6050 library already in platformio.ini (no dependency changes needed)
- Command schema needs complete overhaul to match new command set
- Motor driver interface needs alignment with BTS7960 specifications
- All motion commands must integrate with balance controller (not independent)

---

## Next Steps

1. Review and approve this plan
2. Begin Phase 1 implementation
3. Test incrementally after each phase
4. Adjust plan based on findings during implementation
