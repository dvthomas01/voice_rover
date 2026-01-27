#!/usr/bin/env python3
"""Test script for the complete audio pipeline.

This script demonstrates the full audio pipeline:
1. Load audio file (WAV format)
2. Transcribe with Whisper
3. Parse commands
4. Show parsed commands in JSON format

Usage:
    python scripts/test_audio_pipeline.py <audio_file.wav>
    python scripts/test_audio_pipeline.py tests/pi/audio_samples/single_command.wav
"""

import sys
import json
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pi.whisper.transcriber import WhisperTranscriber
from pi.command_parser.parser import CommandParser
from pi.command_queue.queue_manager import CommandQueueManager
from pi.command_parser.command_schema import Command


def command_to_dict(cmd: Command) -> dict:
    """Convert Command object to dictionary for JSON serialization."""
    return {
        "type": cmd.command_type.value,
        "parameters": cmd.parameters,
        "priority": cmd.priority
    }


def test_audio_pipeline(audio_file: str):
    """Test the complete audio pipeline with an audio file.
    
    Args:
        audio_file: Path to WAV audio file
    """
    print("=" * 70)
    print("AUDIO PIPELINE TEST")
    print("=" * 70)
    print(f"\nAudio file: {audio_file}\n")
    
    # Check if file exists
    if not os.path.exists(audio_file):
        print(f"❌ Error: Audio file not found: {audio_file}")
        return
    
    # Step 1: Load Whisper model
    print("Step 1: Loading Whisper model...")
    transcriber = WhisperTranscriber()
    try:
        transcriber.load_model()
        print("✅ Whisper model loaded successfully")
    except Exception as e:
        print(f"❌ Error loading Whisper model: {e}")
        return
    
    # Step 2: Transcribe audio
    print("\nStep 2: Transcribing audio...")
    try:
        transcription = transcriber.transcribe_file(audio_file)
        print(f"✅ Transcription: \"{transcription}\"")
    except Exception as e:
        print(f"❌ Error transcribing audio: {e}")
        return
    
    if not transcription.strip():
        print("⚠️  Warning: Empty transcription")
        return
    
    # Step 3: Parse commands
    print("\nStep 3: Parsing commands...")
    parser = CommandParser()
    try:
        commands = parser.parse(transcription)
        if commands is None or len(commands) == 0:
            print("⚠️  Warning: No commands parsed from transcription")
            print(f"   Transcription was: \"{transcription}\"")
            return
        print(f"✅ Parsed {len(commands)} command(s)")
    except Exception as e:
        print(f"❌ Error parsing commands: {e}")
        return
    
    # Step 4: Enqueue commands
    print("\nStep 4: Enqueueing commands...")
    queue = CommandQueueManager(max_size=100)
    for cmd in commands:
        queue.enqueue(cmd)
    print(f"✅ Enqueued {queue.size()} command(s)")
    
    # Step 5: Display results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    print(f"\n📝 Transcription:")
    print(f"   \"{transcription}\"")
    
    print(f"\n🎯 Parsed Commands ({len(commands)}):")
    for i, cmd in enumerate(commands, 1):
        print(f"\n   Command {i}:")
        print(f"   - Type: {cmd.command_type.value}")
        print(f"   - Priority: {cmd.priority}")
        print(f"   - Parameters: {json.dumps(cmd.parameters, indent=6)}")
    
    print(f"\n📦 Queue Status:")
    print(f"   - Size: {queue.size()}")
    print(f"   - Empty: {queue.is_empty()}")
    
    # Step 6: JSON output
    print(f"\n📄 JSON Output (for ESP32):")
    commands_json = [command_to_dict(cmd) for cmd in commands]
    print(json.dumps(commands_json, indent=2))
    
    # Step 7: Queue execution order
    print(f"\n🔄 Execution Order (dequeue sequence):")
    execution_order = []
    while not queue.is_empty():
        cmd = queue.dequeue()
        execution_order.append(cmd)
        print(f"   {len(execution_order)}. {cmd.command_type.value} (priority: {cmd.priority})")
    
    print("\n" + "=" * 70)
    print("✅ Pipeline test complete!")
    print("=" * 70)


def test_wake_word_status():
    """Check if Porcupine access key is set."""
    print("\n" + "=" * 70)
    print("WAKE WORD DETECTOR STATUS")
    print("=" * 70)
    
    access_key = os.getenv('PORCUPINE_ACCESS_KEY', '')
    
    if access_key:
        print(f"\n✅ Porcupine access key is set")
        print(f"   Key (first 20 chars): {access_key[:20]}...")
        print(f"\n💡 To test wake word detection:")
        print(f"   1. Run the main controller: python pi/main_controller.py")
        print(f"   2. Speak 'jarvis' followed by a command")
        print(f"   3. The system will detect wake word and process your command")
    else:
        print(f"\n⚠️  Porcupine access key is NOT set")
        print(f"\n💡 To enable wake word detection:")
        print(f"   1. Get a free key from: https://console.picovoice.ai/")
        print(f"   2. Set environment variable:")
        print(f"      export PORCUPINE_ACCESS_KEY='your-key-here'")
        print(f"   3. Or add to ~/.zshrc:")
        print(f"      echo 'export PORCUPINE_ACCESS_KEY=\"your-key-here\"' >> ~/.zshrc")
        print(f"      source ~/.zshrc")
        print(f"\n   Note: Without the key, wake word detection is disabled")
        print(f"         but the system will still work (you can test with audio files)")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_audio_pipeline.py <audio_file.wav>")
        print("\nExample:")
        print("  python scripts/test_audio_pipeline.py tests/pi/audio_samples/single_command.wav")
        print("\nAvailable test files:")
        test_dir = Path("tests/pi/audio_samples")
        if test_dir.exists():
            for f in test_dir.glob("*.wav"):
                print(f"  - {f}")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    
    # Test wake word status
    test_wake_word_status()
    
    # Test audio pipeline
    test_audio_pipeline(audio_file)


if __name__ == "__main__":
    main()
