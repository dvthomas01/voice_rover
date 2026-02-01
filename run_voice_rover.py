#!/usr/bin/env python3
"""Run Voice Rover main controller.

This is the main entry point for Voice Rover on Raspberry Pi.
Connects all components: audio → wake word → transcription → commands → ESP32

Usage:
    python run_voice_rover.py
    
    Or make it executable:
    chmod +x run_voice_rover.py
    ./run_voice_rover.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Run main controller
from pi.main_controller import main

if __name__ == "__main__":
    main()
