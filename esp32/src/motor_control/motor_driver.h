#ifndef MOTOR_DRIVER_H
#define MOTOR_DRIVER_H

#include <Arduino.h>

/**
 * Motor driver interface for controlling DC motors.
 * Supports PWM speed control and direction switching.
 */
class MotorDriver {
public:
    /**
     * Initialize motor driver with pin assignments (BTS7960).
     *
     * @param pwm_pin PWM pin for speed control
     * @param r_en_pin Right enable pin (R_EN on BTS7960)
     * @param l_en_pin Left enable pin (L_EN on BTS7960)
     * @param ledc_channel LEDC channel (0-15, must be unique per motor)
     */
    MotorDriver(int pwm_pin, int r_en_pin, int l_en_pin, int ledc_channel);

    /**
     * Initialize motor driver hardware (setup pins, LEDC PWM).
     */
    void begin();

    /**
     * Set motor speed and direction.
     *
     * @param speed Motor speed (-255 to 255)
     *              Negative values = reverse, positive = forward
     */
    void setSpeed(int speed);

    /**
     * Stop the motor immediately.
     * Unconditional safety stop - callable from anywhere.
     */
    void stop();

    /**
     * Get current motor speed.
     *
     * @return Current speed (-255 to 255)
     */
    int getSpeed();

private:
    int pwm_pin_;
    int r_en_pin_;  // Right enable (forward direction)
    int l_en_pin_;  // Left enable (reverse direction)
    int ledc_channel_;  // LEDC channel for this motor
    int current_speed_;

    /**
     * Set motor direction using BTS7960 enable pins.
     * Forward: R_EN=HIGH, L_EN=LOW
     * Reverse: R_EN=LOW, L_EN=HIGH
     * Stop: R_EN=LOW, L_EN=LOW
     */
    void setDirection(bool forward);
};

#endif // MOTOR_DRIVER_H
