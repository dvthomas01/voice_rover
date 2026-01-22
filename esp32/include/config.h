#ifndef CONFIG_H
#define CONFIG_H

// Serial communication
#define SERIAL_BAUDRATE 115200
#define SERIAL_TIMEOUT 1000  // milliseconds

// Motor driver pins (BTS7960)
// BTS7960 uses: PWM for speed, R_EN and L_EN for direction
// Forward: R_EN=HIGH, L_EN=LOW, PWM=speed
// Reverse: R_EN=LOW, L_EN=HIGH, PWM=speed
// Stop: R_EN=LOW, L_EN=LOW, PWM=0
#define MOTOR_LEFT_PWM 25
#define MOTOR_LEFT_R_EN 26
#define MOTOR_LEFT_L_EN 27
#define MOTOR_RIGHT_PWM 32
#define MOTOR_RIGHT_R_EN 33
#define MOTOR_RIGHT_L_EN 34

// Encoder pins (Dagu RS034)
// Must be interrupt-capable pins
#define ENCODER_LEFT_A 18
#define ENCODER_LEFT_B 19
#define ENCODER_RIGHT_A 16
#define ENCODER_RIGHT_B 17

// IMU I2C pins (MPU6050)
#define I2C_SDA 21
#define I2C_SCL 22
#define I2C_FREQ 400000  // 400kHz I2C speed

// PID controller parameters (tune these for your robot)
// Start with KP only, then add KD, finally KI
#define KP 40.0   // Proportional gain
#define KI 0.5    // Integral gain
#define KD 2.0    // Derivative gain

// Balance controller settings
#define BALANCE_LOOP_FREQ 100  // Hz (10ms period) - CRITICAL: Must maintain this frequency
#define BALANCE_ANGLE_OFFSET 0.0  // degrees (calibrated offset)
#define MAX_TILT_ANGLE 45.0  // degrees (fall detection threshold)
#define FALL_DETECTION_THRESHOLD 40.0  // degrees (emergency stop threshold)

// Motor control settings
#define MAX_MOTOR_SPEED 255
#define DEFAULT_MOTOR_SPEED 102  // 0.4 * 255
#define MIN_MOTOR_SPEED 50       // Minimum speed for reliable movement
#define PWM_FREQUENCY 20000       // 20kHz PWM frequency for BTS7960

// Encoder settings
#define ENCODER_PULSES_PER_REV 8  // Low-res: 8 pulses/rev (encoder on output shaft)
// OR #define ENCODER_PULSES_PER_REV 948  // High-res: 948 pulses/rev (encoder on motor shaft)
#define WHEEL_DIAMETER_MM 65      // Dagu RS034 wheel diameter
#define WHEELBASE_MM 150          // Distance between wheels (adjust for your chassis)

// Command execution
#define COMMAND_QUEUE_SIZE 50
#define COMMAND_TIMEOUT_MS 5000   // Timeout for command execution

#endif // CONFIG_H
