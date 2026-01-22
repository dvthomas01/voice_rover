#include "encoder_reader.h"

// Static instance pointers for interrupt handlers
EncoderReader* EncoderReader::instance_a_ = nullptr;
EncoderReader* EncoderReader::instance_b_ = nullptr;

EncoderReader::EncoderReader(int pinA, int pinB)
    : pin_a_(pinA), pin_b_(pinB), position_(0), velocity_(0.0),
      last_update_time_(0), last_position_(0) {
}

void EncoderReader::begin() {
    // TODO: Setup encoder pins
    pinMode(pin_a_, INPUT_PULLUP);
    pinMode(pin_b_, INPUT_PULLUP);
    
    // TODO: Attach interrupts
    // Note: ESP32 uses different interrupt attachment than Arduino
    // attachInterrupt(digitalPinToInterrupt(pin_a_), handleInterruptA, CHANGE);
    // attachInterrupt(digitalPinToInterrupt(pin_b_), handleInterruptB, CHANGE);
    
    // Store instance for interrupt handlers
    instance_a_ = this;
    instance_b_ = this;
    
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

void EncoderReader::handleInterruptA() {
    if (instance_a_) {
        instance_a_->handlePulse(true);
    }
}

void EncoderReader::handleInterruptB() {
    if (instance_b_) {
        instance_b_->handlePulse(false);
    }
}

void EncoderReader::handlePulse(bool channelA) {
    // TODO: Implement quadrature decoding
    // 
    // Quadrature encoding uses two channels 90° out of phase
    // Direction determined by which channel leads
    // 
    // Channel A leads Channel B = Forward
    // Channel B leads Channel A = Reverse
    // 
    // Example implementation:
    // bool a_state = digitalRead(pin_a_);
    // bool b_state = digitalRead(pin_b_);
    // 
    // if (channelA) {
    //     if (a_state == b_state) {
    //         position_++;  // Forward
    //     } else {
    //         position_--;  // Reverse
    //     }
    // } else {
    //     if (a_state == b_state) {
    //         position_--;  // Reverse
    //     } else {
    //         position_++;  // Forward
    //     }
    // }
    
    // Simple increment for now (replace with quadrature decoding)
    if (channelA) {
        position_++;
    } else {
        position_--;
    }
}
