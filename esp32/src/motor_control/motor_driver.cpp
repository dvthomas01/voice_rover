#include "motor_driver.h"

MotorDriver::MotorDriver(int pwm_pin, int dir1_pin, int dir2_pin)
    : pwm_pin_(pwm_pin), dir1_pin_(dir1_pin), dir2_pin_(dir2_pin),
      current_speed_(0) {
}

void MotorDriver::begin() {
    pinMode(pwm_pin_, OUTPUT);
    pinMode(dir1_pin_, OUTPUT);
    pinMode(dir2_pin_, OUTPUT);

    // Initialize PWM
    // To be implemented: Configure PWM frequency and resolution

    stop();
}

void MotorDriver::setSpeed(int speed) {
    // To be implemented: Set motor speed with direction control
    current_speed_ = speed;
}

void MotorDriver::stop() {
    digitalWrite(dir1_pin_, LOW);
    digitalWrite(dir2_pin_, LOW);
    analogWrite(pwm_pin_, 0);
    current_speed_ = 0;
}

int MotorDriver::getSpeed() {
    return current_speed_;
}

void MotorDriver::setDirection(bool forward) {
    if (forward) {
        digitalWrite(dir1_pin_, HIGH);
        digitalWrite(dir2_pin_, LOW);
    } else {
        digitalWrite(dir1_pin_, LOW);
        digitalWrite(dir2_pin_, HIGH);
    }
}
