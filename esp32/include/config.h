#ifndef CONFIG_H
#define CONFIG_H

// Serial communication
#define SERIAL_BAUDRATE 115200
#define SERIAL_TIMEOUT 1000  // milliseconds

// Motor driver pins (BTS7960)
// BTS7960 typically uses: PWM for speed, direction pins for forward/reverse
#define MOTOR_LEFT_PWM 25
#define MOTOR_LEFT_DIR 26
#define MOTOR_RIGHT_PWM 32
#define MOTOR_RIGHT_DIR 33

// Encoder pins (Dagu RS034)
#define ENCODER_LEFT_A 18
#define ENCODER_LEFT_B 19
#define ENCODER_RIGHT_A 16
#define ENCODER_RIGHT_B 17

// Motor control settings
#define MAX_MOTOR_SPEED 255
#define DEFAULT_MOTOR_SPEED 102  // 0.4 * 255
#define MIN_MOTOR_SPEED 50       // Minimum speed for reliable movement

// Command execution
#define COMMAND_QUEUE_SIZE 50

#endif // CONFIG_H
