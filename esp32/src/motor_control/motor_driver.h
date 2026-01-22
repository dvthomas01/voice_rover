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
     * Initialize motor driver with pin assignments.
     *
     * @param pwm_pin PWM pin for speed control
     * @param dir1_pin Direction control pin 1
     * @param dir2_pin Direction control pin 2
     */
    MotorDriver(int pwm_pin, int dir1_pin, int dir2_pin);

    /**
     * Initialize motor driver hardware (setup pins, PWM).
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
    int dir1_pin_;
    int dir2_pin_;
    int current_speed_;

    void setDirection(bool forward);
};

#endif // MOTOR_DRIVER_H
