#include <Arduino.h>
#include <Wire.h>
#include "balance/balance_controller.h"
#include "motor_control/motor_driver.h"
#include "sensors/imu.h"
#include "sensors/encoder_reader.h"
#include "command_handler/command_handler.h"
#include "../include/config.h"

// Global objects
BalanceController balanceController(KP, KI, KD);
MotorDriver leftMotor(MOTOR_LEFT_PWM, MOTOR_LEFT_R_EN, MOTOR_LEFT_L_EN);
MotorDriver rightMotor(MOTOR_RIGHT_PWM, MOTOR_RIGHT_R_EN, MOTOR_RIGHT_L_EN);
IMU imu;
EncoderReader leftEncoder(ENCODER_LEFT_A, ENCODER_LEFT_B);
EncoderReader rightEncoder(ENCODER_RIGHT_A, ENCODER_RIGHT_B);
CommandHandler commandHandler(&balanceController, &leftMotor, &rightMotor, &leftEncoder, &rightEncoder);

// State variables
String serialBuffer = "";
unsigned long lastBalanceUpdate = 0;
bool balance_active = false;

void setup() {
    // Initialize serial communication
    Serial.begin(SERIAL_BAUDRATE);
    delay(1000);  // Wait for serial monitor
    Serial.println("Voice Rover ESP32 Initializing...");

    // Initialize I2C for IMU
    Wire.begin(I2C_SDA, I2C_SCL);
    Wire.setClock(I2C_FREQ);

    // Initialize IMU
    if (!imu.begin()) {
        Serial.println("ERROR: IMU initialization failed!");
        while(1) delay(100);  // Halt if IMU fails
    }
    Serial.println("IMU initialized");

    // Calibrate IMU (robot must be level and stationary)
    Serial.println("Calibrating IMU... Place robot level and stationary");
    delay(2000);
    imu.calibrate();
    Serial.println("IMU calibrated");

    // Initialize encoders
    leftEncoder.begin();
    rightEncoder.begin();
    Serial.println("Encoders initialized");

    // Initialize motors
    leftMotor.begin();
    rightMotor.begin();
    Serial.println("Motors initialized");

    // Initialize command handler
    commandHandler.begin();
    Serial.println("Command handler initialized");

    Serial.println("Voice Rover ESP32 Ready - Entering balance mode");
    balance_active = true;
}

void loop() {
    // CRITICAL: Balance control loop - runs at fixed 100Hz frequency
    // This loop must never be disabled during operation
    unsigned long currentTime = millis();
    if (currentTime - lastBalanceUpdate >= (1000 / BALANCE_LOOP_FREQ)) {
        lastBalanceUpdate = currentTime;

        // Update IMU readings
        if (!imu.update()) {
            Serial.println("WARNING: IMU update failed");
        }

        // Get sensor data
        float angle = imu.getPitchAngle();
        float angular_velocity = imu.getAngularVelocity();
        
        // Get encoder velocities (optional, for feedforward)
        float left_velocity = leftEncoder.getVelocity();
        float right_velocity = rightEncoder.getVelocity();
        float avg_wheel_velocity = (left_velocity + right_velocity) / 2.0;

        // Update balance controller
        balanceController.update(angle, angular_velocity, avg_wheel_velocity);

        // Balance output already includes velocity_setpoint; main applies rotation as L/R diff
        float motorOutput = balanceController.getMotorOutput();
        float rot = balanceController.getRotationSetpoint();
        int left_speed = (int)(motorOutput + rot);
        int right_speed = (int)(motorOutput - rot);
        left_speed = constrain(left_speed, -MAX_MOTOR_SPEED, MAX_MOTOR_SPEED);
        right_speed = constrain(right_speed, -MAX_MOTOR_SPEED, MAX_MOTOR_SPEED);
        leftMotor.setSpeed(left_speed);
        rightMotor.setSpeed(right_speed);

        // Check if robot has fallen
        if (!balanceController.isBalanced()) {
            Serial.println("ERROR: Robot fallen - emergency stop");
            leftMotor.stop();
            rightMotor.stop();
            balanceController.setNeutral();
            balance_active = false;
        }
    }

    // Process serial commands (non-blocking)
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

    // Update encoders (for velocity calculation)
    leftEncoder.update();
    rightEncoder.update();
}
