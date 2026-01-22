#ifndef ENCODER_READER_H
#define ENCODER_READER_H

#include <Arduino.h>

/**
 * Quadrature encoder reader for Dagu RS034 encoders.
 * Reads encoder pulses via interrupts and calculates position/velocity.
 * 
 * INTEGRATION POINT: Balance controller uses getVelocity() for feedback
 * INTEGRATION POINT: Command handler uses getPosition() for distance/angle tracking
 */
class EncoderReader {
public:
    /**
     * Initialize encoder with pin assignments.
     * 
     * @param pinA Encoder channel A pin (must support interrupts)
     * @param pinB Encoder channel B pin (must support interrupts)
     */
    EncoderReader(int pinA, int pinB);

    /**
     * Setup encoder pins and attach interrupts.
     * Must be called in setup().
     */
    void begin();

    /**
     * Get current encoder position (total pulses).
     * Positive = forward, Negative = backward
     * 
     * @return Position in pulses
     */
    long getPosition() const;

    /**
     * Get current wheel velocity.
     * Calculated from position change over time.
     * 
     * @return Velocity in pulses per second
     */
    float getVelocity();

    /**
     * Reset encoder position to zero.
     */
    void reset();

    /**
     * Update velocity calculation.
     * Should be called periodically (e.g., every balance loop cycle).
     */
    void update();

    /**
     * Static interrupt handler for channel A.
     * Must be attached in begin().
     */
    static void handleInterruptA();

    /**
     * Static interrupt handler for channel B.
     * Must be attached in begin().
     */
    static void handleInterruptB();

private:
    int pin_a_;
    int pin_b_;
    volatile long position_;      // Current position (pulses)
    float velocity_;              // Calculated velocity (pulses/sec)
    unsigned long last_update_time_;
    long last_position_;
    
    // Static instances for interrupt handlers
    static EncoderReader* instance_a_;
    static EncoderReader* instance_b_;
    
    /**
     * Handle encoder pulse (called from interrupt).
     * Determines direction based on quadrature encoding.
     */
    void handlePulse(bool channelA);
};

#endif // ENCODER_READER_H
