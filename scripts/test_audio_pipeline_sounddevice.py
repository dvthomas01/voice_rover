#!/usr/bin/env python3
"""Test script for audio pipeline with sounddevice.

Tests the new sounddevice-based audio capture with Whisper transcription
and command parsing to verify the hybrid implementation works.

Usage:
    python scripts/test_audio_pipeline_sounddevice.py
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pi.audio_input.microphone import MicrophoneInterface
from pi.whisper.transcriber import WhisperTranscriber
from pi.command_parser.parser import CommandParser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    print("=" * 60)
    print("Audio Pipeline Test (sounddevice)")
    print("=" * 60)
    print("\nThis test will:")
    print("1. Initialize microphone with sounddevice (16kHz float32)")
    print("2. Load Whisper model")
    print("3. Capture audio for 8 seconds when you speak")
    print("4. Transcribe with Whisper")
    print("5. Parse commands")
    print("\nPress Ctrl+C to exit.\n")
    print("-" * 60)
    
    # Initialize components
    mic = MicrophoneInterface()
    transcriber = WhisperTranscriber()
    parser = CommandParser()
    
    try:
        # Start microphone
        logger.info("Starting microphone...")
        mic.start()
        logger.info("Microphone started successfully")
        
        # Load Whisper model
        logger.info("Loading Whisper model (this may take a moment)...")
        transcriber.load_model()
        logger.info("Whisper model loaded")
        
        print("\n" + "=" * 60)
        print("Ready! Speak a command and press Enter when done.")
        print("=" * 60)
        print("\nExample commands:")
        print("  - jarvis move forward")
        print("  - jarvis turn left 90 degrees")
        print("  - jarvis make a square")
        print("  - jarvis stop")
        print()
        
        while True:
            input("\nPress Enter to start recording (8 seconds)...")
            
            print("\n[Recording...]", end="", flush=True)
            
            # Capture audio for 8 seconds
            audio_data = mic.capture_audio(duration=8.0)
            
            if len(audio_data) == 0:
                print(" No audio captured")
                continue
            
            print(f" Captured {len(audio_data)} samples")
            print("[Transcribing...]", end="", flush=True)
            
            # Transcribe
            text = transcriber.transcribe(audio_data)
            
            if not text:
                print(" No speech detected")
                continue
            
            print(f'\n\nHeard: "{text}"')
            
            # Parse commands
            commands = parser.parse(text)
            
            if commands:
                print(f"\nCommands detected ({len(commands)}):")
                for i, cmd in enumerate(commands, 1):
                    print(f"  {i}. {cmd.command_type.value}", end="")
                    if cmd.parameters:
                        print(f" - parameters: {cmd.parameters}", end="")
                    print(f" (priority: {cmd.priority})")
            else:
                print("  (no valid commands detected)")
            
            print("\n" + "-" * 60)
    
    except KeyboardInterrupt:
        print("\n\nExiting...")
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    
    finally:
        # Cleanup
        logger.info("Cleaning up...")
        mic.stop()
        transcriber.unload_model()
        logger.info("Cleanup complete")


if __name__ == "__main__":
    main()
