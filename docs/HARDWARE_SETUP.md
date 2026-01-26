# Voice Rover Hardware Setup Guide

This document provides detailed instructions for assembling the Voice Rover hardware.

## Component List

### Core Electronics

| Component | Specification | Quantity | Notes |
|-----------|---------------|----------|-------|
| Raspberry Pi 4 | 2GB+ RAM | 1 | 4GB recommended for faster Whisper |
| ESP32 DevKit | ESP32-WROOM-32 | 1 | Any ESP32 dev board works |
| USB Microphone | **Samson Go Mic USB** | 1 | 44.1kHz/48kHz, 16-bit, plug-and-play |
| IMU Sensor | MPU6050 or MPU9250 | 1 | I2C interface |
| Motor Driver | L298N, DRV8833, or TB6612FNG | 1-2 | **3A+ per channel required** (for RS034 stall current) |
| DC Motors | **Dagu RS034 Motor Kit** | 2 | 3-6V, 48:1 or 118.5:1 gear ratio |
| Motor Wheels | **65mm (included with RS034)** | 2 | Rubber for traction |
| Encoders | **Dagu RS034 Hall-effect** | 2 | 8 or 948 pulses/rev (depends on mounting) |

### Power Supply

| Component | Specification | Quantity | Notes |
|-----------|---------------|----------|-------|
| LiPo Battery | 7.4V-11.1V (2S-3S) | 1 | 2200mAh+ recommended |
| Buck Converter | 5V 3A output | 1 | For Raspberry Pi |
| Battery Monitor | Voltage alarm | 1 | Safety feature |

### Mechanical

| Component | Specification | Quantity | Notes |
|-----------|---------------|----------|-------|
| Chassis | Two-wheel balancing | 1 | Custom or kit (e.g., BASYS) |
| Standoffs | M3 or M2.5 | 10+ | For mounting electronics |
| Screws | M3 or M2.5 | 20+ | Various lengths |
| Mounting Plate | Acrylic or aluminum | 1-2 | For stacking electronics |

### Cables and Connectors

- USB-A to Micro-USB cable (Pi to ESP32)
- Dupont jumper wires (male-female, male-male)
- JST connectors for battery (optional)
- Heat shrink tubing

## Pin Assignments

### ESP32 Pins

#### Motor Driver (Left Motor)
- **GPIO 25**: PWM control
- **GPIO 26**: Direction 1
- **GPIO 27**: Direction 2

#### Motor Driver (Right Motor)
- **GPIO 32**: PWM control
- **GPIO 33**: Direction 1
- **GPIO 34**: Direction 2

#### Motor Encoders (Dagu RS034)
- **Left Encoder A**: GPIO 18 (interrupt-capable, with 10kΩ pull-up)
- **Left Encoder B**: GPIO 19 (interrupt-capable, with 10kΩ pull-up)
- **Right Encoder A**: GPIO 16 (interrupt-capable, with 10kΩ pull-up)
- **Right Encoder B**: GPIO 17 (interrupt-capable, with 10kΩ pull-up)
- **Encoder VCC**: 3.3V or 5V (check encoder board requirement)
- **Encoder GND**: Common ground

#### IMU (I2C)
- **GPIO 21**: SDA (I2C Data)
- **GPIO 22**: SCL (I2C Clock)
- **3.3V**: Power
- **GND**: Ground

#### Serial Communication
- **USB**: Connected to Raspberry Pi via USB cable
  - Provides power to ESP32 (if sufficient)
  - Serial TX/RX handled by USB-UART bridge

### Raspberry Pi Pins

- **USB Port**: Microphone input
- **USB Port**: ESP32 connection (data + power)
- **5V Power**: From buck converter or dedicated power supply

## Wiring Diagram

### Power Distribution

```
LiPo Battery (7.4V-11.1V)
    ├─→ Voltage Regulator IN (5V, 6A+)
    │       └─→ Voltage Regulator OUT (5V) → Motor Driver VIN
    │           (RS034 motors require 3-6V, use 5V regulated)
    ├─→ Buck Converter IN
    │       └─→ Buck Converter OUT (5V) → Raspberry Pi
    └─→ ESP32 VIN (optional, or powered via USB from Pi)
```

**Important**: RS034 motors operate at 3-6V, not typical 7.4V-12V. Use voltage regulator to step down battery voltage to 5V for motors.

### Motor Connections

```
ESP32 GPIO 25 (PWM) ──→ Motor Driver ENA
ESP32 GPIO 26 (DIR1) ──→ Motor Driver IN1
ESP32 GPIO 27 (DIR2) ──→ Motor Driver IN2
Motor Driver OUT1 ──→ Left Motor Terminal 1 (RS034)
Motor Driver OUT2 ──→ Left Motor Terminal 2 (RS034)

ESP32 GPIO 32 (PWM) ──→ Motor Driver ENB
ESP32 GPIO 33 (DIR1) ──→ Motor Driver IN3
ESP32 GPIO 34 (DIR2) ──→ Motor Driver IN4
Motor Driver OUT3 ──→ Right Motor Terminal 1 (RS034)
Motor Driver OUT4 ──→ Right Motor Terminal 2 (RS034)

5V Regulator OUT ──→ Motor Driver VCC (3-6V required, use 5V)
Battery (-) ──→ Motor Driver GND
ESP32 GND ──→ Motor Driver GND (common ground)
```

**Note**: RS034 motors require 3-6V. Do not connect battery directly (7.4V+ will damage motors). Use voltage regulator.

### Encoder Connections (Dagu RS034)

```
Left Encoder:
  Channel A ──→ ESP32 GPIO 18 (with 10kΩ pull-up to 3.3V)
  Channel B ──→ ESP32 GPIO 19 (with 10kΩ pull-up to 3.3V)
  VCC ──→ 3.3V or 5V (check encoder board)
  GND ──→ Common ground

Right Encoder:
  Channel A ──→ ESP32 GPIO 16 (with 10kΩ pull-up to 3.3V)
  Channel B ──→ ESP32 GPIO 17 (with 10kΩ pull-up to 3.3V)
  VCC ──→ 3.3V or 5V (check encoder board)
  GND ──→ Common ground
```

**Note**: Encoders are open-drain output. Pull-up resistors required if not built into ESP32 or encoder board.

### IMU Connection

```
ESP32 3.3V ──→ MPU6050 VCC
ESP32 GND ──→ MPU6050 GND
ESP32 GPIO 21 (SDA) ──→ MPU6050 SDA
ESP32 GPIO 22 (SCL) ──→ MPU6050 SCL
```

### USB Serial Connection

```
Raspberry Pi USB Port ──[USB Cable]──→ ESP32 Micro-USB Port
```

## Assembly Instructions

### Step 1: Mechanical Assembly

1. Assemble the two-wheel balancing chassis according to kit instructions
2. Mount motors to the chassis with proper alignment
3. Attach wheels to motor shafts
4. Install mounting plates for electronics using standoffs

### Step 2: Motor Driver Installation

1. Mount motor driver to lower plate
2. Connect motor terminals to driver outputs
   - Ensure correct polarity (test direction later)
3. Connect battery power to motor driver VIN and GND
4. Do NOT connect ESP32 yet

### Step 3: IMU Installation

1. Mount IMU sensor at center of chassis
   - Orientation matters: ensure X-axis points forward
2. Connect IMU to ESP32 using jumper wires (I2C pins)
3. Keep wires short to reduce noise

### Step 4: ESP32 Installation

1. Mount ESP32 to upper plate
2. Connect motor driver signal pins to ESP32 GPIOs
3. Connect common ground between ESP32 and motor driver
4. Connect USB cable from ESP32 to Raspberry Pi (not yet powered)

### Step 5: Raspberry Pi Installation

1. Mount Raspberry Pi to upper plate
2. Connect buck converter output to Raspberry Pi power
3. Plug USB microphone into Raspberry Pi USB port
4. Connect USB cable to ESP32

### Step 6: Power System

1. Install battery holder or mount battery with velcro
2. Connect battery to buck converter
3. Connect battery to motor driver
4. Install battery monitor/voltage alarm (recommended)
5. Add power switch between battery and system (optional but recommended)

### Step 7: Cable Management

1. Secure all wires with zip ties or velcro straps
2. Ensure no wires obstruct wheels or moving parts
3. Label connections for easy troubleshooting
4. Check that IMU sensor is not mechanically stressed

## Testing and Calibration

### Power-On Sequence

1. **First power-on** (ESP32 only):
   - Connect USB to computer (not Pi yet)
   - Upload firmware via PlatformIO
   - Monitor serial output to verify boot

2. **Motor direction test**:
   - Power motor driver with **5V regulated supply** (not battery directly)
   - Send test commands to verify motor direction
   - Swap motor terminals if direction is reversed
   - **Warning**: Do not exceed 6V on RS034 motors

3. **Encoder test**:
   - Manually rotate wheel and verify encoder pulses counted
   - Check encoder resolution (8 or 948 pulses per revolution)
   - Verify direction detection (forward vs backward)
   - Calibrate pulses to distance conversion

4. **IMU calibration**:
   - Place robot on level surface
   - Run IMU calibration routine
   - Note offsets in configuration file

5. **Balance tuning**:
   - Adjust PID parameters in `esp32/include/config.h`
   - Start with low gains and increase gradually
   - Test balance by gently tilting robot

6. **Full system test**:
   - Power Raspberry Pi
   - Start voice controller software
   - Test wake word and simple commands

### Safety Checks

Before operating:

- [ ] All electrical connections secure
- [ ] No exposed wiring or short circuit risk
- [ ] Battery voltage within safe range
- [ ] Motors can move freely without obstruction
- [ ] Emergency stop accessible (physical switch or STOP command)
- [ ] IMU sensor properly mounted and calibrated
- [ ] USB connection to Pi stable

## Troubleshooting

### Motors not responding
- **Check motor voltage**: RS034 requires 3-6V (use 5V regulator, not battery directly)
- Verify motor driver can handle 3A+ per channel (stall current)
- Check motor driver power connections
- Verify GPIO pins match configuration in `config.h`
- Test motor driver with separate 5V power supply
- Check for common ground between ESP32 and driver

### Encoders not counting
- Verify pull-up resistors (10kΩ) are connected to encoder channels
- Check encoder power supply (3.3V or 5V as required)
- Verify GPIO pins have interrupts enabled
- Test encoder output with multimeter or oscilloscope
- Check encoder mounting (output shaft vs motor shaft affects resolution)

### IMU reading errors
- Verify I2C connections (SDA, SCL)
- Check I2C address (usually 0x68 for MPU6050)
- Ensure pull-up resistors present (usually built into IMU board)
- Try slower I2C clock speed

### ESP32 not detected by Raspberry Pi
- Check USB cable (must support data, not just power)
- Verify permissions: `sudo usermod -a -G dialout $USER`
- Check with `ls /dev/ttyUSB*` or `dmesg | grep tty`
- Try different USB port on Pi

### Robot falls over immediately
- Recalibrate IMU on level surface
- Adjust PID gains (reduce if oscillating, increase if too slow)
- Check motor directions match expected behavior
- Verify battery voltage is sufficient

### Intermittent serial communication
- Use high-quality USB cable with shielding
- Add ferrite beads to reduce EMI
- Ensure stable power supply to ESP32
- Check for loose connections

## Maintenance

- **Weekly**: Check battery voltage, tighten loose screws
- **Monthly**: Clean motor contacts, verify IMU calibration
- **As needed**: Replace worn wheels, recharge/replace battery

## Safety Warnings

- Never operate with damaged battery
- Do not exceed motor driver current ratings
- Keep fingers away from wheels during operation
- Test in open area away from stairs or drop-offs
- Implement software timeout for emergency stop
- Monitor battery temperature during operation

## Recommended Tools

- Soldering iron and solder
- Wire strippers
- Multimeter (essential for debugging)
- Screwdriver set (Phillips and hex)
- Heat gun for heat shrink tubing
- Helping hands or PCB holder
- Label maker or masking tape for labeling

## Additional Resources

- MPU6050 Datasheet: [Link to datasheet]
- L298N Motor Driver Guide: [Link to guide]
- ESP32 Pinout Reference: [Link to pinout]
- PlatformIO Documentation: https://docs.platformio.org/
