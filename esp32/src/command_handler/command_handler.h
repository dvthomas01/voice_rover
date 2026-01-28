#ifndef COMMAND_HANDLER_H
#define COMMAND_HANDLER_H

#include <Arduino.h>
#include <ArduinoJson.h>
#include "../include/config.h"

// Forward declarations
class BalanceController;
class MotorDriver;
class EncoderReader;

/**
 * Command handler for parsing and executing commands from Raspberry Pi.
 * Commands are received as newline-delimited JSON over serial.
 * 
 * INTEGRATION POINT: Commands modify balance controller setpoints
 * INTEGRATION POINT: STOP command clears queue and returns to neutral balance
 */
class CommandHandler {
public:
    /**
     * Initialize command handler with required components.
     * 
     * @param balance_controller Balance controller instance
     * @param left_motor Left motor driver
     * @param right_motor Right motor driver
     * @param left_encoder Left encoder reader
     * @param right_encoder Right encoder reader
     */
    CommandHandler(BalanceController* balance_controller,
                   MotorDriver* left_motor,
                   MotorDriver* right_motor,
                   EncoderReader* left_encoder,
                   EncoderReader* right_encoder);

    /**
     * Initialize command handler (setup, etc.).
     */
    void begin();

    /**
     * Parse and execute a command from JSON string.
     * All inputs must be validated to prevent malformed commands.
     *
     * @param json_string JSON command string
     * @return true if command executed successfully
     */
    bool processCommand(const String& json_string);

    /**
     * Execute a primitive movement command.
     * Commands modify balance controller setpoints, don't replace balance control.
     *
     * @param command Command type (e.g., "move_forward", "rotate_clockwise")
     * @param params Command parameters (speed, angle, duration, etc.)
     * @return true if command valid and executed
     */
    bool executePrimitiveCommand(const String& command, JsonObject params);

    /**
     * Execute an intermediate command.
     * Intermediate commands may expand to multiple primitives or use encoders.
     *
     * @param command Command type (e.g., "turn_left", "move_forward_for_time")
     * @param params Command parameters
     * @return true if command valid and executed
     */
    bool executeIntermediateCommand(const String& command, JsonObject params);

    /**
     * Execute STOP command immediately.
     * Clears command queue and returns balance controller to neutral.
     * Balance loop continues running.
     */
    void executeStop();

    /**
     * Send response back to Raspberry Pi.
     *
     * @param success Whether command succeeded
     * @param message Optional message
     */
    void sendResponse(bool success, const String& message = "");

    /**
     * Update command execution (for time-based commands).
     * Should be called periodically to check command completion.
     */
    void update();

private:
    BalanceController* balance_controller_;
    MotorDriver* left_motor_;
    MotorDriver* right_motor_;
    EncoderReader* left_encoder_;
    EncoderReader* right_encoder_;

    // Command queue (FIFO) with copied primitives (safe for persistence)
    struct Command {
        String type;
        unsigned long start_time;
        // Copied parameters (no JsonObject lifetime issues)
        float speed;
        float duration;
        float angle;
        float target_angle;  // For angle-based commands (encoder target)
        float target_distance;  // For distance-based commands (if needed)
    };
    
    static const int MAX_QUEUE_SIZE = COMMAND_QUEUE_SIZE;
    Command command_queue_[MAX_QUEUE_SIZE];
    int queue_head_;
    int queue_tail_;
    int queue_size_;

    bool validateCommand(JsonDocument& doc);
    void clearQueue();
    bool enqueueCommand(const String& command, float speed, float duration, float angle);
    void processQueue();
    
    // Helper functions
    float speedToMotorValue(float speed);  // Convert 0.0-1.0 to -255 to 255
    float pulsesToDistance(long pulses);   // Convert encoder pulses to distance
    float pulsesToAngle(long left_pulses, long right_pulses);  // Convert encoder diff to angle
};

#endif // COMMAND_HANDLER_H
