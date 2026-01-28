#include "motor_driver.h"
#include "../include/config.h"

MotorDriver::MotorDriver(int pwm_pin, int r_en_pin, int l_en_pin, int ledc_channel)
    : pwm_pin_(pwm_pin), r_en_pin_(r_en_pin), l_en_pin_(l_en_pin),
      ledc_channel_(ledc_channel), current_speed_(0) {
}

void MotorDriver::begin() {
    // Setup enable pins as outputs
    pinMode(r_en_pin_, OUTPUT);
    pinMode(l_en_pin_, OUTPUT);

    // Configure LEDC for ESP32 PWM
    // Resolution: 8-bit (0-255)
    // Frequency: 20kHz (from config.h)
    ledcSetup(ledc_channel_, PWM_FREQUENCY, 8);
    ledcAttachPin(pwm_pin_, ledc_channel_);

    stop();
}

void MotorDriver::setSpeed(int speed) {
    // Clamp to valid range
    speed = constrain(speed, -MAX_MOTOR_SPEED, MAX_MOTOR_SPEED);
    
    if (speed == 0) {
        stop();
        return;
    }
    
    // Set direction based on sign
    setDirection(speed > 0);
    
    // Write PWM duty cycle using LEDC
    ledcWrite(ledc_channel_, abs(speed));
    
    current_speed_ = speed;
}

void MotorDriver::stop() {
    // BTS7960 stop: Both enables LOW, PWM duty 0
    digitalWrite(r_en_pin_, LOW);
    digitalWrite(l_en_pin_, LOW);
    ledcWrite(ledc_channel_, 0);
    current_speed_ = 0;
}

int MotorDriver::getSpeed() {
    return current_speed_;
}

void MotorDriver::setDirection(bool forward) {
    // BTS7960 direction control:
    // Forward: R_EN=HIGH, L_EN=LOW
    // Reverse: R_EN=LOW, L_EN=HIGH
    if (forward) {
        digitalWrite(r_en_pin_, HIGH);
        digitalWrite(l_en_pin_, LOW);
    } else {
        digitalWrite(r_en_pin_, LOW);
        digitalWrite(l_en_pin_, HIGH);
    }
}
