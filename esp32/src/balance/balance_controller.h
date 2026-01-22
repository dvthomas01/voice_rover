#ifndef BALANCE_CONTROLLER_H
#define BALANCE_CONTROLLER_H

/**
 * PID-based balance controller for self-balancing rover.
 *
 * This controller maintains balance by continuously reading IMU data
 * and adjusting motor speeds based on the tilt angle.
 */
class BalanceController {
public:
    /**
     * Initialize balance controller with PID parameters.
     *
     * @param kp Proportional gain
     * @param ki Integral gain
     * @param kd Derivative gain
     */
    BalanceController(float kp, float ki, float kd);

    /**
     * Update the controller with current sensor readings.
     * Must be called at a consistent frequency (e.g., 100Hz).
     * 
     * CRITICAL: This function must never be disabled during operation.
     *
     * @param angle Current tilt angle in degrees
     * @param angular_velocity Angular velocity in degrees/sec
     * @param wheel_velocity Optional wheel velocity from encoders (for feedforward)
     */
    void update(float angle, float angular_velocity, float wheel_velocity = 0.0);

    /**
     * Get the computed motor output.
     *
     * @return Motor speed adjustment (-255 to 255)
     */
    float getMotorOutput();

    /**
     * Set velocity setpoint for forward/backward motion.
     * Motion commands modify this setpoint, which is added to balance control.
     * 
     * @param velocity Target velocity (positive = forward, negative = backward)
     */
    void setVelocitySetpoint(float velocity);

    /**
     * Set rotation setpoint for turning.
     * 
     * @param angular_velocity Target angular velocity (positive = clockwise, negative = counterclockwise)
     */
    void setRotationSetpoint(float angular_velocity);

    /**
     * Return to neutral balance (no motion setpoints).
     * Called by STOP command.
     */
    void setNeutral();

    /**
     * Reset the controller state (clear integral, error history).
     */
    void reset();

    /**
     * Check if robot is within stable balance range.
     *
     * @return true if balanced, false if falling
     */
    bool isBalanced();

    /**
     * Get current velocity setpoint.
     * 
     * @return Velocity setpoint
     */
    float getVelocitySetpoint() const;

    /**
     * Get current rotation setpoint.
     * 
     * @return Rotation setpoint
     */
    float getRotationSetpoint() const;

private:
    float kp_, ki_, kd_;
    float integral_;
    float previous_error_;
    float motor_output_;
    unsigned long last_update_time_;
    
    // Motion setpoints (modify balance, don't replace it)
    float velocity_setpoint_;     // Forward/backward velocity
    float rotation_setpoint_;     // Rotation angular velocity
    
    // PID calculation
    float calculatePID(float angle, float angular_velocity);
    
    // Integral windup protection
    void limitIntegral();
};

#endif // BALANCE_CONTROLLER_H
