#!/bin/bash
# ESP32 firmware flashing script for Voice Rover

set -e  # Exit on error

echo "Voice Rover - ESP32 Firmware Flash"
echo "=================================="

# Check if PlatformIO is installed
if ! command -v pio &> /dev/null; then
    echo "ERROR: PlatformIO not found"
    echo "Install with: pip install platformio"
    exit 1
fi

# Check if esp32 directory exists
if [ ! -d "esp32" ]; then
    echo "ERROR: esp32 directory not found"
    echo "Run this script from the voice_rover root directory"
    exit 1
fi

# Navigate to esp32 directory
cd esp32

# Detect ESP32 port
echo ""
echo "Step 1: Detecting ESP32..."
if ls /dev/ttyUSB* &> /dev/null; then
    ESP32_PORT=$(ls /dev/ttyUSB* | head -n 1)
    echo "ESP32 detected at: $ESP32_PORT"
elif ls /dev/cu.usbserial* &> /dev/null; then
    ESP32_PORT=$(ls /dev/cu.usbserial* | head -n 1)
    echo "ESP32 detected at: $ESP32_PORT"
else
    echo "WARNING: ESP32 not detected"
    echo "Connect ESP32 via USB and try again"
    exit 1
fi

# Clean previous build (optional)
if [ "$1" == "--clean" ]; then
    echo ""
    echo "Step 2: Cleaning previous build..."
    pio run -t clean
fi

# Build firmware
echo ""
echo "Step 2: Building firmware..."
pio run

# Upload firmware
echo ""
echo "Step 3: Uploading firmware to ESP32..."
pio run -t upload --upload-port $ESP32_PORT

# Monitor serial output
echo ""
echo "Firmware uploaded successfully!"
echo ""
echo "Starting serial monitor (Ctrl+C to exit)..."
sleep 2
pio device monitor --port $ESP32_PORT
