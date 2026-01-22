#include "balance_controller.h"
#include <Arduino.h>
#include "../include/config.h"

BalanceController::BalanceController(float kp, float ki, float kd)
    : kp_(kp), ki_(ki), kd_(kd), integral_(0.0), previous_error_(0.0),
      motor_output_(0.0), last_update_time_(0),
      velocity_setpoint_(0.0), rotation_setpoint_(0.0) {
}

void BalanceController::update(float angle, float angular_velocity, float wheel_velocity) {
    // TODO: Implement PID balance control
    // 
    // CRITICAL: This function must run at 100Hz and never be disabled
    // 
    // Algorithm:
    // 1. Calculate error: target_angle - current_angle
    //    - Target angle = BALANCE_ANGLE_OFFSET (typically 0°)
    //    - Current angle = angle parameter
    // 
    // 2. Calculate PID terms:
    //    - P term = kp * error
    //    - I term = ki * integral (with windup protection)
    //    - D term = kd * (error - previous_error) / dt
    // 
    // 3. Optional: Add velocity feedforward from wheel_velocity
    // 
    // 4. Add motion setpoints:
    //    - Balance output + velocity_setpoint_ + rotation_setpoint_
    // 
    // 5. Clamp output to motor limits
    // 
    // 6. Update state for next iteration
    
    unsigned long current_time = millis();
    float dt = (current_time - last_update_time_) / 1000.0;
    if (dt <= 0) dt = 0.01;  // Prevent division by zero
    
    // Calculate PID output
    motor_output_ = calculatePID(angle, angular_velocity);
    
    // TODO: Add motion setpoints
    // motor_output_ += velocity_setpoint_;
    // motor_output_ += rotation_setpoint_;
    
    // Clamp output
    motor_output_ = constrain(motor_output_, -MAX_MOTOR_SPEED, MAX_MOTOR_SPEED);
    
    last_update_time_ = current_time;
}

float BalanceController::getMotorOutput() {
    return motor_output_;
}

void BalanceController::setVelocitySetpoint(float velocity) {
    // TODO: Set velocity setpoint for forward/backward motion
    // This modifies balance control, doesn't replace it
    velocity_setpoint_ = velocity;
}

void BalanceController::setRotationSetpoint(float angular_velocity) {
    // TODO: Set rotation setpoint for turning
    rotation_setpoint_ = angular_velocity;
}

void BalanceController::setNeutral() {
    // TODO: Clear motion setpoints, return to balance-only mode
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
    // TODO: Check if angle is within acceptable range
    // Use MAX_TILT_ANGLE from config.h
    // Return false if robot has fallen (emergency stop)
    
    // Example:
    // float current_angle = ...;  // Need to track current angle
    // return abs(current_angle) < MAX_TILT_ANGLE;
    
    return true;  // Placeholder
}

float BalanceController::getVelocitySetpoint() const {
    return velocity_setpoint_;
}

float BalanceController::getRotationSetpoint() const {
    return rotation_setpoint_;
}

float BalanceController::calculatePID(float angle, float angular_velocity) {
    // TODO: Implement PID calculation
    // 
    // 1. Calculate error (target angle - current angle)
    float target_angle = BALANCE_ANGLE_OFFSET;
    float error = target_angle - angle;
    
    // 2. Calculate P term
    float p_term = kp_ * error;
    
    // 3. Calculate I term (with windup protection)
    integral_ += error * 0.01;  // dt = 0.01 (100Hz)
    limitIntegral();
    float i_term = ki_ * integral_;
    
    // 4. Calculate D term
    float d_term = kd_ * (error - previous_error_) / 0.01;
    previous_error_ = error;
    
    // 5. Combine terms
    float output = p_term + i_term + d_term;
    
    return output;
}

void BalanceController::limitIntegral() {
    // TODO: Implement integral windup protection
    // Limit integral to prevent excessive accumulation
    // Example:
    // float max_integral = 100.0;  // Adjust based on tuning
    // if (integral_ > max_integral) integral_ = max_integral;
    // if (integral_ < -max_integral) integral_ = -max_integral;
}
