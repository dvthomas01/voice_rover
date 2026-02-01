/**
 * PID Tuning Mode for Voice Rover ESP32
 * 
 * This program logs real-time balance controller data to help tune PID gains.
 * 
 * USAGE:
 * 1. Upload this to ESP32
 * 2. Open Serial Monitor (115200 baud)
 * 3. Hold robot upright manually at first
 * 4. Send commands via Serial to tune gains
 * 5. Collect data and analyze with MATLAB scripts
 * 
 * SERIAL COMMANDS:
 * - "log"       : Start/stop data logging
 * - "reset"     : Reset integral and clear history
 * - "kp=XX.X"   : Set proportional gain
 * - "ki=XX.X"   : Set integral gain
 * - "kd=XX.X"   : Set derivative gain
 * - "gains"     : Print current PID gains
 * - "help"      : Show all commands
 */

#include <Arduino.h>
#include <Wire.h>
#include "balance/balance_controller.h"
#include "motor_control/motor_driver.h"
#include "sensors/imu.h"
#include "../include/config.h"

// Global objects
BalanceController balanceController(KP, KI, KD);
MotorDriver leftMotor(MOTOR_LEFT_PWM, MOTOR_LEFT_R_EN, MOTOR_LEFT_L_EN, 0);
MotorDriver rightMotor(MOTOR_RIGHT_PWM, MOTOR_RIGHT_R_EN, MOTOR_RIGHT_L_EN, 1);
IMU imu;

// Tuning state
bool logging_enabled = false;
unsigned long lastBalanceUpdate = 0;
unsigned long log_count = 0;
String serialBuffer = "";

void printHelp() {
    Serial.println("\n========== PID TUNING MODE ==========");
    Serial.println("Commands:");
    Serial.println("  log        - Start/stop data logging");
    Serial.println("  reset      - Reset controller (clear integral)");
    Serial.println("  kp=XX.X    - Set proportional gain (e.g., kp=40.0)");
    Serial.println("  ki=XX.X    - Set integral gain (e.g., ki=0.5)");
    Serial.println("  kd=XX.X    - Set derivative gain (e.g., kd=2.0)");
    Serial.println("  gains      - Print current PID gains");
    Serial.println("  help       - Show this help message");
    Serial.println("\nTuning Strategy:");
    Serial.println("  1. Start with KP only (KI=0, KD=0)");
    Serial.println("  2. Increase KP until oscillation begins");
    Serial.println("  3. Add KD to dampen oscillation");
    Serial.println("  4. Add small KI to eliminate steady-state error");
    Serial.println("\nData Format (CSV):");
    Serial.println("  time,angle,angular_vel,motor_out,p_term,i_term,d_term,error,integral");
    Serial.println("=====================================\n");
}

void printGains() {
    float kp, ki, kd;
    balanceController.getGains(kp, ki, kd);
    Serial.print("Current PID Gains: KP=");
    Serial.print(kp, 2);
    Serial.print(", KI=");
    Serial.print(ki, 2);
    Serial.print(", KD=");
    Serial.println(kd, 2);
}

void processCommand(String cmd) {
    cmd.trim();
    cmd.toLowerCase();
    
    if (cmd == "log") {
        logging_enabled = !logging_enabled;
        if (logging_enabled) {
            Serial.println("Logging STARTED");
            Serial.println("time,angle,angular_vel,motor_out,p_term,i_term,d_term,error,integral");
            log_count = 0;
        } else {
            Serial.println("Logging STOPPED");
            Serial.print("Logged ");
            Serial.print(log_count);
            Serial.println(" samples");
        }
    }
    else if (cmd == "reset") {
        balanceController.reset();
        Serial.println("Controller RESET (integral cleared)");
    }
    else if (cmd.startsWith("kp=")) {
        float new_kp = cmd.substring(3).toFloat();
        float ki, kd;
        balanceController.getGains(ki, ki, kd); // Get current KI, KD
        balanceController.setGains(new_kp, ki, kd);
        Serial.print("KP set to: ");
        Serial.println(new_kp, 2);
        printGains();
    }
    else if (cmd.startsWith("ki=")) {
        float new_ki = cmd.substring(3).toFloat();
        float kp, kd;
        balanceController.getGains(kp, kd, kd); // Get current KP, KD
        balanceController.setGains(kp, new_ki, kd);
        Serial.print("KI set to: ");
        Serial.println(new_ki, 2);
        printGains();
        Serial.println("NOTE: Integral reset to prevent windup");
        balanceController.reset(); // Reset integral when changing KI
    }
    else if (cmd.startsWith("kd=")) {
        float new_kd = cmd.substring(3).toFloat();
        float kp, ki;
        balanceController.getGains(kp, ki, ki); // Get current KP, KI
        balanceController.setGains(kp, ki, new_kd);
        Serial.print("KD set to: ");
        Serial.println(new_kd, 2);
        printGains();
    }
    else if (cmd == "gains") {
        printGains();
    }
    else if (cmd == "help") {
        printHelp();
    }
    else {
        Serial.println("Unknown command. Type 'help' for commands.");
    }
}

void setup() {
    // Initialize serial
    Serial.begin(SERIAL_BAUDRATE);
    delay(2000);
    
    Serial.println("\n\n");
    Serial.println("╔════════════════════════════════════╗");
    Serial.println("║   PID TUNING MODE - Voice Rover   ║");
    Serial.println("╚════════════════════════════════════╝");
    Serial.println();
    
    // Initialize I2C
    Wire.begin(I2C_SDA, I2C_SCL);
    Wire.setClock(I2C_FREQ);
    
    // Initialize IMU
    Serial.print("Initializing IMU... ");
    if (!imu.begin()) {
        Serial.println("FAILED!");
        Serial.println("ERROR: IMU not detected. Check wiring.");
        while(1) {
            delay(1000);
            Serial.println("Halted. Please reset after fixing IMU connection.");
        }
    }
    Serial.println("OK");
    
    // Calibrate IMU
    Serial.println("\n>>> CALIBRATION <<<");
    Serial.println("Place robot LEVEL and STATIONARY");
    Serial.println("Calibrating in 3 seconds...");
    delay(3000);
    imu.calibrate();
    Serial.println("Calibration complete!\n");
    
    // Initialize motors
    leftMotor.begin();
    rightMotor.begin();
    Serial.println("Motors initialized");
    
    // Print initial gains
    printGains();
    printHelp();
    
    Serial.println("\n>>> READY TO TUNE <<<");
    Serial.println("Hold robot upright and type 'log' to start logging\n");
}

void loop() {
    // Balance control loop at 100Hz
    unsigned long currentTime = millis();
    if (currentTime - lastBalanceUpdate >= (1000 / BALANCE_LOOP_FREQ)) {
        lastBalanceUpdate = currentTime;
        
        // Update IMU
        if (!imu.update()) {
            // IMU update failed, but don't halt - just log warning
            if (log_count % 100 == 0) { // Print every 100 failures
                Serial.println("WARNING: IMU update failed");
            }
            return;
        }
        
        // Get sensor data
        float angle = imu.getPitchAngle();
        float angular_velocity = imu.getAngularVelocity();
        
        // Update balance controller
        balanceController.update(angle, angular_velocity, 0.0);
        
        // Get motor output
        float motor_output = balanceController.getMotorOutput();
        
        // Apply to motors
        int left_speed = (int)motor_output;
        int right_speed = (int)motor_output;
        left_speed = constrain(left_speed, -MAX_MOTOR_SPEED, MAX_MOTOR_SPEED);
        right_speed = constrain(right_speed, -MAX_MOTOR_SPEED, MAX_MOTOR_SPEED);
        leftMotor.setSpeed(left_speed);
        rightMotor.setSpeed(right_speed);
        
        // Check if fallen (but don't stop motors in tuning mode - let user handle it)
        if (!balanceController.isBalanced()) {
            if (log_count % 10 == 0) { // Print occasionally
                Serial.println("WARNING: Angle exceeds threshold - robot may be falling!");
            }
        }
        
        // Log data if enabled
        if (logging_enabled) {
            // Get PID term values
            float p_term = balanceController.getPTerm();
            float i_term = balanceController.getITerm();
            float d_term = balanceController.getDTerm(angular_velocity);
            float error = balanceController.getError();
            float integral = balanceController.getIntegral();
            
            // CSV format: time,angle,angular_vel,motor_out,p_term,i_term,d_term,error,integral
            Serial.print(currentTime);
            Serial.print(",");
            Serial.print(angle, 3);
            Serial.print(",");
            Serial.print(angular_velocity, 3);
            Serial.print(",");
            Serial.print(motor_output, 2);
            Serial.print(",");
            Serial.print(p_term, 2);
            Serial.print(",");
            Serial.print(i_term, 2);
            Serial.print(",");
            Serial.print(d_term, 2);
            Serial.print(",");
            Serial.print(error, 3);
            Serial.print(",");
            Serial.println(integral, 3);
            
            log_count++;
            
            // Auto-stop after 10 seconds (1000 samples at 100Hz)
            if (log_count >= 1000) {
                logging_enabled = false;
                Serial.println("\nLogging auto-stopped after 1000 samples (10 seconds)");
                Serial.println("Type 'log' to start again, or copy data above for analysis");
            }
        }
    }
    
    // Process serial commands (non-blocking)
    while (Serial.available() > 0) {
        char c = Serial.read();
        if (c == '\n' || c == '\r') {
            if (serialBuffer.length() > 0) {
                processCommand(serialBuffer);
                serialBuffer = "";
            }
        } else {
            serialBuffer += c;
        }
    }
}
