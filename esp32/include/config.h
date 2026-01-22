#ifndef CONFIG_H
#define CONFIG_H

// Serial communication
#define SERIAL_BAUDRATE 115200
#define SERIAL_TIMEOUT 1000  // milliseconds

// Motor pins (example - adjust for your hardware)
#define MOTOR_LEFT_PWM 25
#define MOTOR_LEFT_DIR1 26
#define MOTOR_LEFT_DIR2 27
#define MOTOR_RIGHT_PWM 32
#define MOTOR_RIGHT_DIR1 33
#define MOTOR_RIGHT_DIR2 34

// IMU I2C pins
#define I2C_SDA 21
#define I2C_SCL 22

// PID controller parameters (tune these for your robot)
#define KP 40.0
#define KI 0.5
#define KD 2.0

// Balance controller settings
#define BALANCE_LOOP_FREQ 100  // Hz
#define BALANCE_ANGLE_OFFSET 0.0  // degrees
#define MAX_MOTOR_SPEED 255

// Command execution
#define COMMAND_QUEUE_SIZE 50

#endif // CONFIG_H
