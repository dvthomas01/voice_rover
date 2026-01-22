#ifndef IMU_H
#define IMU_H

#include <Arduino.h>
#include <Adafruit_MPU6050.h>
#include <Wire.h>

/**
 * IMU sensor interface for MPU6050.
 * Provides pitch angle and angular velocity for balance control.
 * 
 * INTEGRATION POINT: Balance controller uses getPitchAngle() and getAngularVelocity()
 */
class IMU {
public:
    /**
     * Constructor.
     */
    IMU();

    /**
     * Initialize IMU sensor.
     * Must be called in setup() before use.
     * 
     * @return true if initialization successful
     */
    bool begin();

    /**
     * Update IMU readings and calculate pitch angle.
     * Should be called at balance loop frequency (100Hz).
     * 
     * @return true if update successful
     */
    bool update();

    /**
     * Get current pitch angle in degrees.
     * Positive = leaning forward, Negative = leaning backward
     * 
     * @return Pitch angle in degrees
     */
    float getPitchAngle() const;

    /**
     * Get angular velocity in degrees/second.
     * 
     * @return Angular velocity (degrees/sec)
     */
    float getAngularVelocity() const;

    /**
     * Check if IMU is calibrated.
     * 
     * @return true if calibrated
     */
    bool isCalibrated() const;

    /**
     * Calibrate IMU on level surface.
     * Robot must be stationary and level when called.
     * 
     * TODO: Implement calibration routine
     */
    void calibrate();

    /**
     * Check if IMU data is valid.
     * 
     * @return true if sensor is working correctly
     */
    bool isValid() const;

private:
    Adafruit_MPU6050 mpu_;
    sensors_event_t accel_, gyro_, temp_;
    
    float pitch_angle_;           // Calculated pitch angle (degrees)
    float angular_velocity_;      // Angular velocity (degrees/sec)
    float pitch_offset_;          // Calibration offset
    bool calibrated_;
    bool valid_;
    unsigned long last_update_time_;
    
    // Complementary filter parameters
    float alpha_;  // Filter coefficient (0.0-1.0)
    
    /**
     * Calculate pitch angle from accelerometer and gyroscope.
     * Uses complementary filter to combine sensor data.
     * 
     * TODO: Implement complementary filter or Kalman filter
     */
    void calculatePitch();
};

#endif // IMU_H
