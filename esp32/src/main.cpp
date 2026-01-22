#include <Arduino.h>
#include <Wire.h>
#include "balance/balance_controller.h"
#include "motor_control/motor_driver.h"
#include "command_handler/command_handler.h"
#include "../include/config.h"

// Global objects
BalanceController balanceController(KP, KI, KD);
MotorDriver leftMotor(MOTOR_LEFT_PWM, MOTOR_LEFT_DIR1, MOTOR_LEFT_DIR2);
MotorDriver rightMotor(MOTOR_RIGHT_PWM, MOTOR_RIGHT_DIR1, MOTOR_RIGHT_DIR2);
CommandHandler commandHandler;

// State variables
String serialBuffer = "";
unsigned long lastBalanceUpdate = 0;

void setup() {
    // Initialize serial communication
    Serial.begin(SERIAL_BAUDRATE);
    Serial.println("Voice Rover ESP32 Initializing...");

    // Initialize I2C for IMU
    Wire.begin(I2C_SDA, I2C_SCL);

    // Initialize motors
    leftMotor.begin();
    rightMotor.begin();

    // Initialize IMU
    // To be implemented: Setup MPU6050 or other IMU

    Serial.println("Voice Rover ESP32 Ready");
}

void loop() {
    // Balance control loop - runs at fixed frequency
    unsigned long currentTime = millis();
    if (currentTime - lastBalanceUpdate >= (1000 / BALANCE_LOOP_FREQ)) {
        lastBalanceUpdate = currentTime;

        // Read IMU data
        // To be implemented: Read angle and angular velocity from IMU
        float angle = 0.0;
        float angular_velocity = 0.0;

        // Update balance controller
        balanceController.update(angle, angular_velocity);

        // Apply motor output
        float motorOutput = balanceController.getMotorOutput();
        // To be implemented: Apply motor output to both motors

        // Check if robot has fallen
        if (!balanceController.isBalanced()) {
            // To be implemented: Emergency stop if fallen
        }
    }

    // Process serial commands
    while (Serial.available() > 0) {
        char c = Serial.read();
        if (c == '\n') {
            // Process complete command
            commandHandler.processCommand(serialBuffer);
            serialBuffer = "";
        } else {
            serialBuffer += c;
        }
    }
}
