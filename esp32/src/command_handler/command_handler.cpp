#include "command_handler.h"
#include "../balance/balance_controller.h"
#include "../motor_control/motor_driver.h"
#include "../sensors/encoder_reader.h"
#include "../include/config.h"

CommandHandler::CommandHandler(BalanceController* balance_controller,
                               MotorDriver* left_motor,
                               MotorDriver* right_motor,
                               EncoderReader* left_encoder,
                               EncoderReader* right_encoder)
    : balance_controller_(balance_controller),
      left_motor_(left_motor),
      right_motor_(right_motor),
      left_encoder_(left_encoder),
      right_encoder_(right_encoder),
      queue_head_(0), queue_tail_(0), queue_size_(0) {
}

void CommandHandler::begin() {
    clearQueue();
    Serial.println("Command handler initialized");
}

bool CommandHandler::processCommand(const String& json_string) {
    // TODO: Parse JSON and route to appropriate handler
    // CRITICAL: Must validate all JSON inputs to prevent crashes
    
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, json_string);
    
    if (error) {
        sendResponse(false, "Invalid JSON: " + String(error.c_str()));
        return false;
    }
    
    // Validate command structure
    if (!validateCommand(doc)) {
        sendResponse(false, "Invalid command structure");
        return false;
    }
    
    String command = doc["command"].as<String>();
    int priority = doc["priority"] | 0;
    
    // Handle STOP command immediately (highest priority)
    if (command == "stop" || priority == 100) {
        executeStop();
        sendResponse(true, "Stop command executed");
        return true;
    }
    
    JsonObject params = doc["parameters"].as<JsonObject>();
    
    // Route to appropriate handler
    // Primitive commands: move_forward, move_backward, rotate_clockwise, rotate_counterclockwise
    if (command == "move_forward" || command == "move_backward" ||
        command == "rotate_clockwise" || command == "rotate_counterclockwise") {
        return executePrimitiveCommand(command, params);
    }
    
    // Intermediate commands: turn_left, turn_right, move_forward_for_time, etc.
    if (command == "turn_left" || command == "turn_right" ||
        command == "move_forward_for_time" || command == "move_backward_for_time" ||
        command == "make_square" || command == "make_circle" || command == "make_star" ||
        command == "zigzag" || command == "spin" || command == "dance") {
        return executeIntermediateCommand(command, params);
    }
    
    sendResponse(false, "Unknown command: " + command);
    return false;
}

bool CommandHandler::executePrimitiveCommand(const String& command, JsonObject params) {
    // TODO: Execute primitive commands by modifying balance controller setpoints
    // 
    // Commands modify balance, don't replace it:
    // - move_forward: Set positive velocity setpoint
    // - move_backward: Set negative velocity setpoint
    // - rotate_clockwise: Set positive rotation setpoint
    // - rotate_counterclockwise: Set negative rotation setpoint
    
    float speed = params["speed"] | 0.4;  // Default speed 0.4
    float motor_speed = speedToMotorValue(speed);
    
    if (command == "move_forward") {
        // TODO: Set forward velocity setpoint
        balance_controller_->setVelocitySetpoint(motor_speed);
        sendResponse(true, "Moving forward");
        return true;
    }
    
    if (command == "move_backward") {
        // TODO: Set backward velocity setpoint
        balance_controller_->setVelocitySetpoint(-motor_speed);
        sendResponse(true, "Moving backward");
        return true;
    }
    
    if (command == "rotate_clockwise") {
        // TODO: Set clockwise rotation setpoint
        balance_controller_->setRotationSetpoint(motor_speed);
        sendResponse(true, "Rotating clockwise");
        return true;
    }
    
    if (command == "rotate_counterclockwise") {
        // TODO: Set counterclockwise rotation setpoint
        balance_controller_->setRotationSetpoint(-motor_speed);
        sendResponse(true, "Rotating counterclockwise");
        return true;
    }
    
    return false;
}

bool CommandHandler::executeIntermediateCommand(const String& command, JsonObject params) {
    // TODO: Execute intermediate commands
    // 
    // Time-based commands: Track duration, clear setpoint when complete
    // Angle-based commands: Use encoder feedback to achieve target angle
    // Pattern commands: Execute sequence of primitives
    
    if (command == "turn_left" || command == "turn_right") {
        // TODO: Implement angle-based turning
        // 1. Get target angle from params
        // 2. Set rotation setpoint
        // 3. Monitor encoder difference until target angle reached
        // 4. Clear rotation setpoint
        
        float angle = params["angle"] | 90.0;
        float speed = params["speed"] | 0.4;
        
        // Enqueue command for tracking
        if (enqueueCommand(command, params)) {
            sendResponse(true, "Turning " + String(angle) + " degrees");
            return true;
        }
        return false;
    }
    
    if (command == "move_forward_for_time" || command == "move_backward_for_time") {
        // TODO: Implement time-based movement
        // 1. Get duration from params
        // 2. Set velocity setpoint
        // 3. Track time, clear setpoint when duration elapsed
        
        float duration = params["duration"] | 1.0;
        float speed = params["speed"] | 0.4;
        
        if (enqueueCommand(command, params)) {
            sendResponse(true, "Moving for " + String(duration) + " seconds");
            return true;
        }
        return false;
    }
    
    // TODO: Implement pattern commands (square, circle, star, zigzag, spin, dance)
    // These expand to sequences of primitive commands
    
    sendResponse(false, "Intermediate command not yet implemented: " + command);
    return false;
}

void CommandHandler::executeStop() {
    // TODO: Immediate stop - highest priority
    // 1. Clear command queue
    // 2. Return balance controller to neutral (clear all setpoints)
    // 3. Balance loop continues running
    
    clearQueue();
    balance_controller_->setNeutral();
    
    Serial.println("STOP command executed - returning to neutral balance");
}

void CommandHandler::sendResponse(bool success, const String& message) {
    StaticJsonDocument<200> doc;
    doc["success"] = success;
    if (message.length() > 0) {
        doc["message"] = message;
    }
    
    serializeJson(doc, Serial);
    Serial.println();
}

void CommandHandler::update() {
    // TODO: Update command execution
    // Check time-based commands for completion
    // Check angle-based commands for completion
    // Process next command in queue when current completes
    
    processQueue();
}

bool CommandHandler::validateCommand(JsonDocument& doc) {
    // TODO: Validate command structure
    // - Check "command" field exists and is string
    // - Check "parameters" field exists and is object
    // - Check "priority" field if present
    // - Validate parameter types and ranges
    
    if (!doc.containsKey("command")) {
        return false;
    }
    
    if (!doc["command"].is<String>()) {
        return false;
    }
    
    if (doc.containsKey("parameters") && !doc["parameters"].is<JsonObject>()) {
        return false;
    }
    
    return true;
}

void CommandHandler::clearQueue() {
    queue_head_ = 0;
    queue_tail_ = 0;
    queue_size_ = 0;
}

bool CommandHandler::enqueueCommand(const String& command, JsonObject params) {
    // TODO: Add command to FIFO queue
    // Check queue not full
    // Store command with start time
    
    if (queue_size_ >= MAX_QUEUE_SIZE) {
        return false;
    }
    
    command_queue_[queue_tail_].type = command;
    command_queue_[queue_tail_].start_time = millis();
    // TODO: Store params and calculate targets
    
    queue_tail_ = (queue_tail_ + 1) % MAX_QUEUE_SIZE;
    queue_size_++;
    return true;
}

void CommandHandler::processQueue() {
    // TODO: Process command queue
    // Check if current command is complete
    // Move to next command if complete
    // Clear setpoints when all commands done
}

float CommandHandler::speedToMotorValue(float speed) {
    // Convert speed (0.0-1.0) to motor value (-255 to 255)
    return constrain(speed * MAX_MOTOR_SPEED, -MAX_MOTOR_SPEED, MAX_MOTOR_SPEED);
}

float CommandHandler::pulsesToDistance(long pulses) {
    // TODO: Convert encoder pulses to distance in meters
    // Formula: distance = (pulses / pulses_per_rev) * wheel_circumference
    float wheel_circumference = PI * WHEEL_DIAMETER_MM / 1000.0;  // meters
    return (pulses / (float)ENCODER_PULSES_PER_REV) * wheel_circumference;
}

float CommandHandler::pulsesToAngle(long left_pulses, long right_pulses) {
    // TODO: Convert encoder difference to rotation angle
    // Formula: angle = (right_pulses - left_pulses) / wheelbase * 180 / PI
    long pulse_diff = right_pulses - left_pulses;
    float distance_diff = pulsesToDistance(pulse_diff);
    return (distance_diff / (WHEELBASE_MM / 1000.0)) * 180.0 / PI;
}
