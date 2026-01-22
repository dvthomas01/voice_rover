#include "command_handler.h"

CommandHandler::CommandHandler() {
}

bool CommandHandler::processCommand(const String& json_string) {
    // To be implemented: Parse JSON and route to appropriate handler
    // CRITICAL: Must validate all JSON inputs to prevent crashes
    return false;
}

bool CommandHandler::executeMovementCommand(const String& command, JsonObject params) {
    // To be implemented: Execute movement commands
    return false;
}

void CommandHandler::executeStop() {
    // To be implemented: Immediate stop - highest priority
    // Must clear command queue and stop all motors
}

void CommandHandler::sendResponse(bool success, const String& message) {
    // To be implemented: Send JSON response over serial
    StaticJsonDocument<200> doc;
    doc["success"] = success;
    if (message.length() > 0) {
        doc["message"] = message;
    }

    serializeJson(doc, Serial);
    Serial.println();
}

bool CommandHandler::validateCommand(JsonDocument& doc) {
    // To be implemented: Validate command structure
    return false;
}
