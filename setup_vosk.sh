#!/bin/bash
# Setup VOSK for Voice Rover on Raspberry Pi
# Run this after cloning the repo

set -e

echo "========================================="
echo "Voice Rover - VOSK Setup"
echo "========================================="
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install core dependencies
echo ""
echo "Installing dependencies..."
pip install numpy
pip install sounddevice
pip install pyserial
pip install pvporcupine
pip install pytest pytest-mock

# Install VOSK
echo ""
echo "Installing VOSK..."
pip install vosk

# Download VOSK model
echo ""
mkdir -p models
cd models

if [ -d "vosk-model-small-en-us-0.15" ]; then
    echo "VOSK model already downloaded"
else
    echo "Downloading VOSK model (40 MB)..."
    wget -q --show-progress https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
    
    echo "Extracting model..."
    unzip -q vosk-model-small-en-us-0.15.zip
    rm vosk-model-small-en-us-0.15.zip
    
    echo "✓ Model downloaded"
fi

cd ..

# Backup original transcriber
echo ""
if [ -f "pi/whisper/transcriber.py" ] && [ ! -f "pi/whisper/transcriber_whisper.py" ]; then
    echo "Backing up original transcriber..."
    cp pi/whisper/transcriber.py pi/whisper/transcriber_whisper.py
fi

# Use VOSK transcriber
echo "Configuring VOSK transcriber..."
if [ -f "pi/whisper/transcriber_vosk.py" ]; then
    cp pi/whisper/transcriber_vosk.py pi/whisper/transcriber.py
    echo "  ✓ Using VOSK"
else
    echo "  ⚠ transcriber_vosk.py not found"
    echo "  Pull latest code from dami branch"
fi

# Verify installations
echo ""
echo "========================================="
echo "Verifying Installation"
echo "========================================="

python -c "import numpy; print('✓ NumPy OK')" || echo "✗ NumPy failed"
python -c "import sounddevice; print('✓ sounddevice OK')" || echo "✗ sounddevice failed"
python -c "from vosk import Model; print('✓ VOSK OK')" || echo "✗ VOSK failed"
python -c "import pvporcupine; print('✓ Porcupine OK')" || echo "✗ Porcupine failed (need API key)"

# Test model loading
if [ -d "models/vosk-model-small-en-us-0.15" ]; then
    python -c "from vosk import Model; m = Model('models/vosk-model-small-en-us-0.15'); print('✓ VOSK model loaded')" || echo "✗ Model loading failed"
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "VOSK Performance on Pi:"
echo "  • Transcription speed: < 1 second (real-time!)"
echo "  • Memory usage: ~300 MB"
echo "  • Accuracy: 85-90% for voice commands"
echo ""
echo "Next steps:"
echo "  1. Set Porcupine API key:"
echo "     export PORCUPINE_ACCESS_KEY='your-key-here'"
echo ""
echo "  2. Test audio pipeline:"
echo "     python scripts/test_audio_pipeline_sounddevice.py"
echo ""
echo "  3. Enjoy real-time voice control! 🎤🤖"
echo ""
echo "To restore Whisper:"
echo "  cp pi/whisper/transcriber_whisper.py pi/whisper/transcriber.py"
echo ""
