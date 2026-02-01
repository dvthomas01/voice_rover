#!/bin/bash
# Quick setup script for Raspberry Pi to fix "Illegal instruction" error
# Run this on your Raspberry Pi after cloning the repo

set -e

echo "========================================="
echo "Voice Rover - Raspberry Pi Setup"
echo "========================================="
echo ""

# Check if running on ARM
ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" && "$ARCH" != "armv7l" ]]; then
    echo "Warning: Not running on ARM architecture ($ARCH)"
    echo "This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Remove problematic packages
echo ""
echo "Removing openai-whisper and PyTorch (if installed)..."
pip uninstall openai-whisper torch torchvision torchaudio -y 2>/dev/null || echo "  (not installed, skipping)"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install numpy
pip install sounddevice
pip install pyserial
pip install pvporcupine

# Install faster-whisper
echo ""
echo "Installing faster-whisper (optimized for Pi)..."
pip install faster-whisper

# Install testing dependencies
pip install pytest pytest-mock

# Backup original transcriber
echo ""
if [ -f "pi/whisper/transcriber.py" ] && [ ! -f "pi/whisper/transcriber_openai.py" ]; then
    echo "Backing up original transcriber..."
    cp pi/whisper/transcriber.py pi/whisper/transcriber_openai.py
fi

# Use faster transcriber
echo "Configuring faster-whisper transcriber..."
if [ -f "pi/whisper/transcriber_faster.py" ]; then
    cp pi/whisper/transcriber_faster.py pi/whisper/transcriber.py
    echo "  ✓ Using faster-whisper"
else
    echo "  ⚠ transcriber_faster.py not found, keeping original"
fi

# Update config for Pi (use tiny model)
echo ""
echo "Updating config for Raspberry Pi..."
if grep -q 'WHISPER_MODEL_SIZE = "base"' pi/config.py; then
    sed -i.bak 's/WHISPER_MODEL_SIZE = "base"/WHISPER_MODEL_SIZE = "tiny"/' pi/config.py
    echo "  ✓ Changed Whisper model to 'tiny' for speed"
else
    echo "  ℹ Config already updated or different format"
fi

# Verify installations
echo ""
echo "========================================="
echo "Verifying Installation"
echo "========================================="

python -c "import numpy; print('✓ NumPy OK')" || echo "✗ NumPy failed"
python -c "import sounddevice; print('✓ sounddevice OK')" || echo "✗ sounddevice failed"
python -c "from faster_whisper import WhisperModel; print('✓ faster-whisper OK')" || echo "✗ faster-whisper failed"
python -c "import pvporcupine; print('✓ Porcupine OK')" || echo "✗ Porcupine failed (need API key)"

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Set Porcupine API key:"
echo "     export PORCUPINE_ACCESS_KEY='your-key-here'"
echo ""
echo "  2. Test audio pipeline:"
echo "     python scripts/test_audio_pipeline_sounddevice.py"
echo ""
echo "  3. If you get 'Illegal instruction', see PI_SETUP_GUIDE.md"
echo ""
echo "To restore original openai-whisper:"
echo "  cp pi/whisper/transcriber_openai.py pi/whisper/transcriber.py"
echo ""
