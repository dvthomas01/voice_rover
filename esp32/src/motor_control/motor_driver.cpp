#include "motor_driver.h"
#include "../include/config.h"

MotorDriver::MotorDriver(int pwm_pin, int r_en_pin, int l_en_pin)
    : pwm_pin_(pwm_pin), r_en_pin_(r_en_pin), l_en_pin_(l_en_pin),
      current_speed_(0) {
}

void MotorDriver::begin() {
    // TODO: Setup pins
    pinMode(pwm_pin_, OUTPUT);
    pinMode(r_en_pin_, OUTPUT);
    pinMode(l_en_pin_, OUTPUT);

    // TODO: Configure PWM frequency for BTS7960 (20kHz recommended)
    // ESP32 uses ledcSetup() for PWM frequency control
    // Example:
    // ledcSetup(0, PWM_FREQUENCY, 8);  // Channel 0, 20kHz, 8-bit resolution
    // ledcAttachPin(pwm_pin_, 0);

    stop();
}

void MotorDriver::setSpeed(int speed) {
    // TODO: Implement BTS7960 speed control
    // - Clamp speed to valid range (-255 to 255)
    // - Set direction based on sign
    // - Set PWM value (absolute value of speed)
    // - Update current_speed_
    
    // Clamp speed
    speed = constrain(speed, -MAX_MOTOR_SPEED, MAX_MOTOR_SPEED);
    
    if (speed == 0) {
        stop();
        return;
    }
    
    // Set direction and PWM
    setDirection(speed > 0);
    analogWrite(pwm_pin_, abs(speed));
    
    current_speed_ = speed;
}

void MotorDriver::stop() {
    // BTS7960 stop: Both enables LOW
    digitalWrite(r_en_pin_, LOW);
    digitalWrite(l_en_pin_, LOW);
    analogWrite(pwm_pin_, 0);
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
