#!/usr/bin/env python3
"""Test script for serial communication with ESP32."""

import serial
import json
import time
import sys

# Configuration
SERIAL_PORT = "/dev/ttyUSB0"  # Adjust as needed
BAUDRATE = 115200
TIMEOUT = 2.0


def test_serial_connection():
    """Test basic serial connection to ESP32."""
    print("Voice Rover - Serial Communication Test")
    print("=" * 40)

    try:
        # Open serial connection
        print(f"\nConnecting to {SERIAL_PORT} at {BAUDRATE} baud...")
        ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=TIMEOUT)
        time.sleep(2)  # Wait for ESP32 to reset

        print("Connected!")
        print("\nReading initial output from ESP32...")
        time.sleep(1)

        # Read any initial output
        while ser.in_waiting:
            line = ser.readline().decode('utf-8').strip()
            if line:
                print(f"  ESP32: {line}")

        # Test commands
        test_commands = [
            {
                "command": "move_forward",
                "parameters": {"distance": 1.0, "speed": 0.5},
                "priority": 0
            },
            {
                "command": "turn_left",
                "parameters": {"angle": 90},
                "priority": 0
            },
            {
                "command": "stop",
                "parameters": {},
                "priority": 100
            }
        ]

        print("\nSending test commands...")
        for i, cmd in enumerate(test_commands, 1):
            print(f"\nTest {i}: {cmd['command']}")

            # Send command
            cmd_json = json.dumps(cmd) + "\n"
            print(f"  Sending: {cmd_json.strip()}")
            ser.write(cmd_json.encode('utf-8'))

            # Wait for response
            time.sleep(0.5)

            # Read response
            if ser.in_waiting:
                response = ser.readline().decode('utf-8').strip()
                print(f"  Response: {response}")

                try:
                    response_json = json.loads(response)
                    if response_json.get('success'):
                        print("  ✓ Success")
                    else:
                        print(f"  ✗ Error: {response_json.get('message')}")
                except json.JSONDecodeError:
                    print(f"  ✗ Invalid JSON response")
            else:
                print("  ✗ No response received")

        # Close connection
        ser.close()
        print("\n" + "=" * 40)
        print("Serial test complete!")

    except serial.SerialException as e:
        print(f"\nERROR: Could not open serial port {SERIAL_PORT}")
        print(f"Details: {e}")
        print("\nTroubleshooting:")
        print("1. Check ESP32 is connected: ls /dev/ttyUSB*")
        print("2. Check permissions: sudo usermod -a -G dialout $USER")
        print("3. Try a different port (update SERIAL_PORT in this script)")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    test_serial_connection()
