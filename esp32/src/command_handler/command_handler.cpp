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
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, json_string);
    
    if (error) {
        sendResponse(false, "JSON parse error: " + String(error.c_str()));
        return false;
    }
    
    // Validate basic structure
    if (!validateCommand(doc)) {
        sendResponse(false, "Missing or invalid command/parameters");
        return false;
    }
    
    String command = doc["command"].as<String>();
    int priority = doc["priority"] | 0;
    
    // STOP command bypass (immediate, highest priority)
    if (command == "stop" || priority == 100) {
        executeStop();
        sendResponse(true, "Emergency stop executed");
        return true;
    }
    
    // Get parameters object (treat missing as empty)
    JsonObject params = doc["parameters"] | doc.createNestedObject("parameters");
    
    // Route to handler based on command type
    if (command == "move_forward" || command == "move_backward" ||
        command == "rotate_clockwise" || command == "rotate_counterclockwise") {
        return executePrimitiveCommand(command, params);
    }
    
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
    // Extract and validate speed parameter
    float speed = params["speed"] | 0.4;  // Default 0.4
    float original_speed = speed;
    
    // Validate speed type
    if (!params["speed"].is<float>() && !params["speed"].isNull()) {
        sendResponse(false, "Invalid speed type (must be numeric)");
        return false;
    }
    
    // Clamp speed to valid range [0.0, 1.0]
    speed = constrain(speed, 0.0f, 1.0f);
    float motor_speed = speedToMotorValue(speed);
    
    // Build response message with clamping info if needed
    String response_msg;
    bool clamped = (speed != original_speed);
    
    if (command == "move_forward") {
        balance_controller_->setVelocitySetpoint(motor_speed);
        response_msg = "Moving forward";
        if (clamped) {
            response_msg += " (speed clamped " + String(original_speed, 2) + " -> " + String(speed, 2) + ")";
        }
        sendResponse(true, response_msg);
        return true;
    }
    
    if (command == "move_backward") {
        balance_controller_->setVelocitySetpoint(-motor_speed);
        response_msg = "Moving backward";
        if (clamped) {
            response_msg += " (speed clamped " + String(original_speed, 2) + " -> " + String(speed, 2) + ")";
        }
        sendResponse(true, response_msg);
        return true;
    }
    
    if (command == "rotate_clockwise") {
        balance_controller_->setRotationSetpoint(motor_speed);
        response_msg = "Rotating clockwise";
        if (clamped) {
            response_msg += " (speed clamped " + String(original_speed, 2) + " -> " + String(speed, 2) + ")";
        }
        sendResponse(true, response_msg);
        return true;
    }
    
    if (command == "rotate_counterclockwise") {
        balance_controller_->setRotationSetpoint(-motor_speed);
        response_msg = "Rotating counterclockwise";
        if (clamped) {
            response_msg += " (speed clamped " + String(original_speed, 2) + " -> " + String(speed, 2) + ")";
        }
        sendResponse(true, response_msg);
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
        // Angle-based turning - not yet implemented (requires processQueue)
        sendResponse(false, "Command not implemented yet: " + command);
        return false;
    }
    
    if (command == "move_forward_for_time" || command == "move_backward_for_time") {
        // Time-based movement - not yet implemented (requires processQueue)
        sendResponse(false, "Command not implemented yet: " + command);
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
    // Validate command field (required, must be string)
    if (!doc.containsKey("command") || !doc["command"].is<String>()) {
        return false;
    }
    
    // Validate parameters field (optional, but if present must be object)
    if (doc.containsKey("parameters") && !doc["parameters"].is<JsonObject>()) {
        return false;
    }
    
    // Validate priority field (optional, but if present must be numeric)
    if (doc.containsKey("priority") && !doc["priority"].is<int>()) {
        return false;
    }
    
    return true;
}

void CommandHandler::clearQueue() {
    queue_head_ = 0;
    queue_tail_ = 0;
    queue_size_ = 0;
}

bool CommandHandler::enqueueCommand(const String& command, float speed, float duration, float angle) {
    // Add command to FIFO queue with copied primitives
    if (queue_size_ >= MAX_QUEUE_SIZE) {
        return false;
    }
    
    Command& cmd = command_queue_[queue_tail_];
    cmd.type = command;
    cmd.start_time = millis();
    cmd.speed = speed;
    cmd.duration = duration;
    cmd.angle = angle;
    cmd.target_angle = 0.0;  // Calculated when execution starts
    cmd.target_distance = 0.0;
    
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
