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
     * @param angle Current tilt angle in degrees
     * @param angular_velocity Angular velocity in degrees/sec
     */
    void update(float angle, float angular_velocity);

    /**
     * Get the computed motor output.
     *
     * @return Motor speed adjustment (-255 to 255)
     */
    float getMotorOutput();

    /**
     * Set target angle offset for moving forward/backward.
     *
     * @param offset Target angle offset in degrees
     */
    void setTargetOffset(float offset);

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

private:
    float kp_, ki_, kd_;
    float integral_;
    float previous_error_;
    float target_offset_;
    float motor_output_;
    unsigned long last_update_time_;
};

#endif // BALANCE_CONTROLLER_H
