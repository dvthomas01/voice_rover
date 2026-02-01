#include "balance_controller.h"
#include <Arduino.h>
#include <math.h>
#include "../include/config.h"

// Sign convention (LOCKED): positive pitch = lean forward, positive motor = wheels forward.
// So: error = angle - target => lean forward => positive error => positive output.

BalanceController::BalanceController(float kp, float ki, float kd)
    : kp_(kp), ki_(ki), kd_(kd), integral_(0.0), previous_error_(0.0),
      motor_output_(0.0), last_update_time_(0), last_angle_(0.0),
      velocity_setpoint_(0.0), rotation_setpoint_(0.0) {
}

void BalanceController::update(float angle, float angular_velocity, float wheel_velocity) {
    // CRITICAL: Run at 100 Hz. Fixed dt = 0.01 s. wheel_velocity unused (reserved for feedforward).
    (void)wheel_velocity;

    last_angle_ = angle;

    float balance_pid = calculatePID(angle, angular_velocity);
    motor_output_ = balance_pid + velocity_setpoint_;
    motor_output_ = constrain(motor_output_, -MAX_MOTOR_SPEED, MAX_MOTOR_SPEED);

    last_update_time_ = millis();
}

float BalanceController::getMotorOutput() {
    return motor_output_;
}

void BalanceController::setVelocitySetpoint(float velocity) {
    velocity_setpoint_ = velocity;
}

void BalanceController::setRotationSetpoint(float angular_velocity) {
    rotation_setpoint_ = angular_velocity;
}

void BalanceController::setNeutral() {
    velocity_setpoint_ = 0.0;
    rotation_setpoint_ = 0.0;
}

void BalanceController::reset() {
    integral_ = 0.0;
    previous_error_ = 0.0;
    motor_output_ = 0.0;
    velocity_setpoint_ = 0.0;
    rotation_setpoint_ = 0.0;
}

bool BalanceController::isBalanced() {
    return fabs(last_angle_) < FALL_DETECTION_THRESHOLD;
}

float BalanceController::getVelocitySetpoint() const {
    return velocity_setpoint_;
}

float BalanceController::getRotationSetpoint() const {
    return rotation_setpoint_;
}

float BalanceController::calculatePID(float angle, float angular_velocity) {
    // Option A: error = angle - target => lean forward => positive output (wheels forward)
    const float target_angle = BALANCE_ANGLE_OFFSET;
    float error = angle - target_angle;

    float p_term = kp_ * error;

    integral_ += error * 0.01f;  // fixed dt = 0.01 (100 Hz)
    limitIntegral();
    float i_term = ki_ * integral_;

    // Derivative on measurement: -Kd * angular_velocity (no derivative kick)
    float d_term = -kd_ * angular_velocity;

    previous_error_ = error;
    return p_term + i_term + d_term;
}

void BalanceController::limitIntegral() {
    integral_ = constrain(integral_, -INTEGRAL_LIMIT, INTEGRAL_LIMIT);
}

// ========== PID TUNING HELPERS ==========

float BalanceController::getPTerm() const {
    const float target_angle = BALANCE_ANGLE_OFFSET;
    float error = last_angle_ - target_angle;
    return kp_ * error;
}

float BalanceController::getITerm() const {
    return ki_ * integral_;
}

float BalanceController::getDTerm(float angular_velocity) const {
    return -kd_ * angular_velocity;
}

float BalanceController::getError() const {
    const float target_angle = BALANCE_ANGLE_OFFSET;
    return last_angle_ - target_angle;
}

float BalanceController::getIntegral() const {
    return integral_;
}

void BalanceController::setGains(float kp, float ki, float kd) {
    kp_ = kp;
    ki_ = ki;
    kd_ = kd;
}

void BalanceController::getGains(float& kp, float& ki, float& kd) const {
    kp = kp_;
    ki = ki_;
    kd = kd_;
}
