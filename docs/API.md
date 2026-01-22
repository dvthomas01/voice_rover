# Voice Rover Communication Protocol

This document specifies the JSON-based communication protocol between the Raspberry Pi and ESP32.

## Overview

- **Transport**: USB Serial (UART)
- **Baud Rate**: 115200
- **Format**: Newline-delimited JSON
- **Direction**: Bidirectional (Pi → ESP32 for commands, ESP32 → Pi for responses)

## Command Format

Commands sent from Raspberry Pi to ESP32:

```json
{
  "command": "<command_type>",
  "parameters": {
    "<param1>": <value1>,
    "<param2>": <value2>
  },
  "priority": <integer>
}
```

### Fields

- **command** (string, required): Command type identifier
- **parameters** (object, optional): Command-specific parameters
- **priority** (integer, optional): Command priority (default: 0, STOP: 100)

## Primitive Commands

### move_forward

Move the rover forward by a specified distance.

```json
{
  "command": "move_forward",
  "parameters": {
    "distance": 2.0,
    "speed": 0.5
  },
  "priority": 0
}
```

**Parameters:**
- `distance` (float, required): Distance in meters
- `speed` (float, optional): Speed multiplier (0.0-1.0), default: 0.5

### move_backward

Move the rover backward by a specified distance.

```json
{
  "command": "move_backward",
  "parameters": {
    "distance": 1.5,
    "speed": 0.5
  },
  "priority": 0
}
```

**Parameters:**
- `distance` (float, required): Distance in meters
- `speed` (float, optional): Speed multiplier (0.0-1.0), default: 0.5

### turn_left

Rotate the rover left by a specified angle.

```json
{
  "command": "turn_left",
  "parameters": {
    "angle": 90
  },
  "priority": 0
}
```

**Parameters:**
- `angle` (float, required): Rotation angle in degrees

### turn_right

Rotate the rover right by a specified angle.

```json
{
  "command": "turn_right",
  "parameters": {
    "angle": 45
  },
  "priority": 0
}
```

**Parameters:**
- `angle` (float, required): Rotation angle in degrees

### stop

Immediately stop all motors and clear the command queue.

```json
{
  "command": "stop",
  "parameters": {},
  "priority": 100
}
```

**Parameters:** None

**Special Behavior:**
- Highest priority (100)
- Bypasses command queue
- Clears all pending commands
- Immediate execution

## Response Format

Responses sent from ESP32 to Raspberry Pi:

```json
{
  "success": <boolean>,
  "message": "<optional_message>",
  "data": {
    "<key>": <value>
  }
}
```

### Fields

- **success** (boolean, required): Whether command succeeded
- **message** (string, optional): Human-readable status or error message
- **data** (object, optional): Additional response data

### Success Response

```json
{
  "success": true,
  "message": "Command executed"
}
```

### Error Response

```json
{
  "success": false,
  "message": "Invalid command: unknown_command"
}
```

## Error Codes

Error messages follow standardized patterns:

- `"Invalid command: <command_name>"`: Unrecognized command type
- `"Missing parameter: <param_name>"`: Required parameter not provided
- `"Invalid parameter: <param_name>"`: Parameter value out of range or wrong type
- `"Robot not balanced"`: Cannot execute command due to balance state
- `"Command queue full"`: Cannot enqueue command (queue at capacity)

## Command Expansion

Intermediate commands are expanded on the Raspberry Pi before transmission. The ESP32 only receives primitive commands.

Example: "Turn around" (intermediate) → `turn_left(180)` (primitive)

### Intermediate Commands and Expansions

| Intermediate | Expansion |
|--------------|-----------|
| turn_around | `turn_left` or `turn_right` with angle=180 |
| circle | Sequence of `move_forward` + `turn_left` with calculated parameters |
| square | 4x sequence: `move_forward` + `turn_right(90)` |

## Protocol Examples

### Example 1: Forward Movement

**Pi → ESP32:**
```json
{"command": "move_forward", "parameters": {"distance": 2.0, "speed": 0.7}, "priority": 0}
```

**ESP32 → Pi:**
```json
{"success": true, "message": "Moving forward 2.0m"}
```

### Example 2: Stop Command

**Pi → ESP32:**
```json
{"command": "stop", "parameters": {}, "priority": 100}
```

**ESP32 → Pi:**
```json
{"success": true, "message": "Emergency stop executed"}
```

### Example 3: Error - Invalid Parameter

**Pi → ESP32:**
```json
{"command": "move_forward", "parameters": {}, "priority": 0}
```

**ESP32 → Pi:**
```json
{"success": false, "message": "Missing parameter: distance"}
```

## Implementation Notes

### Raspberry Pi Side
- Commands serialized using Python's `json.dumps()`
- Newline appended after each command: `json.dumps(cmd) + "\n"`
- Responses parsed using `json.loads()`

### ESP32 Side
- Use ArduinoJson library for parsing
- Read serial until newline character
- Validate all fields before execution
- Always send response, even on error

## Security Considerations

- **Input Validation**: ESP32 must validate all JSON inputs before execution
- **Range Checking**: Verify parameter values are within acceptable ranges
- **Timeout Handling**: Implement timeouts for serial communication
- **Buffer Overflow Protection**: Limit maximum command string length

## Future Extensions

Potential additions to the protocol:

- Status query commands (battery level, IMU data, motor status)
- Configuration commands (PID tuning, speed limits)
- Telemetry streaming from ESP32 to Pi
- Acknowledgment/sequence numbers for reliable delivery
