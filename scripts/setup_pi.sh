#!/bin/bash
# Raspberry Pi setup script for Voice Rover

set -e  # Exit on error

echo "Voice Rover - Raspberry Pi Setup"
echo "================================"

# Check if running on Raspberry Pi (optional)
if [ -f /proc/device-tree/model ]; then
    MODEL=$(cat /proc/device-tree/model)
    echo "Detected: $MODEL"
fi

# Update system
echo ""
echo "Step 1: Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install system dependencies
echo ""
echo "Step 2: Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    portaudio19-dev \
    python3-pyaudio \
    git \
    vim

# Set up Python virtual environment
echo ""
echo "Step 3: Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo ""
echo "Step 4: Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Set up serial port permissions
echo ""
echo "Step 5: Configuring serial port permissions..."
sudo usermod -a -G dialout $USER
echo "Added $USER to dialout group (requires logout/login to take effect)"

# Test microphone
echo ""
echo "Step 6: Testing microphone..."
if arecord -l | grep -q "card"; then
    echo "Microphone detected:"
    arecord -l
else
    echo "WARNING: No microphone detected"
fi

# Check for ESP32 connection
echo ""
echo "Step 7: Checking for ESP32..."
if ls /dev/ttyUSB* &> /dev/null; then
    echo "ESP32 detected at:"
    ls /dev/ttyUSB*
else
    echo "WARNING: No ESP32 detected at /dev/ttyUSB*"
    echo "Connect ESP32 and check with: ls /dev/ttyUSB*"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Logout and login (or reboot) for serial permissions to take effect"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Configure settings in pi/config.py if needed"
echo "4. Run the system: python pi/main_controller.py"
