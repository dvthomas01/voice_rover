#include "encoder_reader.h"

EncoderReader::EncoderReader(int pinA, int pinB)
    : pin_a_(pinA), pin_b_(pinB), position_(0), velocity_(0.0),
      last_update_time_(0), last_position_(0) {
}

void EncoderReader::begin() {
    pinMode(pin_a_, INPUT_PULLUP);
    pinMode(pin_b_, INPUT_PULLUP);
    
    // Use attachInterruptArg to pass 'this' to each ISR
    // This allows multiple encoder instances to work independently
    attachInterruptArg(digitalPinToInterrupt(pin_a_), isrA, this, CHANGE);
    attachInterruptArg(digitalPinToInterrupt(pin_b_), isrB, this, CHANGE);
    
    last_update_time_ = millis();
    last_position_ = position_;
}

long EncoderReader::getPosition() const {
    return position_;
}

float EncoderReader::getVelocity() {
    update();  // Update velocity calculation
    return velocity_;
}

void EncoderReader::reset() {
    position_ = 0;
    last_position_ = 0;
    velocity_ = 0.0;
}

void EncoderReader::update() {
    // TODO: Calculate velocity from position change
    // velocity = (position - last_position) / time_delta
    
    unsigned long current_time = millis();
    float dt = (current_time - last_update_time_) / 1000.0;
    
    if (dt > 0) {
        velocity_ = (position_ - last_position_) / dt;
        last_position_ = position_;
        last_update_time_ = current_time;
    }
}

// Static ISR trampolines - cast arg to EncoderReader* and call instance method
void IRAM_ATTR EncoderReader::isrA(void* arg) {
    EncoderReader* encoder = static_cast<EncoderReader*>(arg);
    encoder->handlePulse(true);
}

void IRAM_ATTR EncoderReader::isrB(void* arg) {
    EncoderReader* encoder = static_cast<EncoderReader*>(arg);
    encoder->handlePulse(false);
}

void IRAM_ATTR EncoderReader::handlePulse(bool channelA) {
    // Minimal quadrature decoding for direction detection
    // Read both pin states to determine direction
    bool a_state = digitalRead(pin_a_);
    bool b_state = digitalRead(pin_b_);
    
    // Quadrature logic: direction depends on which channel leads
    if (channelA) {
        // Channel A changed
        if (a_state == b_state) {
            position_++;  // Forward
        } else {
            position_--;  // Reverse
        }
    } else {
        // Channel B changed
        if (a_state == b_state) {
            position_--;  // Reverse
        } else {
            position_++;  // Forward
        }
    }
}
