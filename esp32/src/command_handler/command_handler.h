#ifndef COMMAND_HANDLER_H
#define COMMAND_HANDLER_H

#include <Arduino.h>
#include <ArduinoJson.h>

/**
 * Command handler for parsing and executing commands from Raspberry Pi.
 * Commands are received as newline-delimited JSON over serial.
 */
class CommandHandler {
public:
    /**
     * Initialize command handler.
     */
    CommandHandler();

    /**
     * Parse and execute a command from JSON string.
     * All inputs must be validated to prevent malformed commands.
     *
     * @param json_string JSON command string
     * @return true if command executed successfully
     */
    bool processCommand(const String& json_string);

    /**
     * Execute a movement command.
     *
     * @param command Command type (e.g., "move_forward", "turn_left")
     * @param params Command parameters (distance, angle, speed, etc.)
     * @return true if command valid and queued
     */
    bool executeMovementCommand(const String& command, JsonObject params);

    /**
     * Execute STOP command immediately.
     * This bypasses the command queue and stops all motors.
     */
    void executeStop();

    /**
     * Send response back to Raspberry Pi.
     *
     * @param success Whether command succeeded
     * @param message Optional message
     */
    void sendResponse(bool success, const String& message = "");

private:
    bool validateCommand(JsonDocument& doc);
};

#endif // COMMAND_HANDLER_H
