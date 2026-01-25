#!/usr/bin/env python3
"""Test script to demonstrate audio file processing with Whisper and command parser.

This script shows the full pipeline:
1. Load audio file
2. Transcribe with Whisper
3. Parse commands
4. Display results

Usage:
    python scripts/test_audio_files.py
    python scripts/test_audio_files.py <audio_file_path>
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pi.whisper.transcriber import WhisperTranscriber
from pi.command_parser.parser import CommandParser
from pi.command_parser.command_schema import CommandType


def test_audio_file(audio_path: str):
    """Test a single audio file through the full pipeline."""
    print(f"\n{'='*70}")
    print(f"Testing: {audio_path}")
    print(f"{'='*70}")
    
    transcriber = WhisperTranscriber()
    parser = CommandParser()
    
    print("\n[1] Transcribing audio with Whisper...")
    try:
        text = transcriber.transcribe_file(audio_path)
        print(f"    Transcribed text: '{text}'")
    except Exception as e:
        print(f"    ERROR: Transcription failed: {e}")
        return
    
    print("\n[2] Parsing commands...")
    try:
        commands = parser.parse(text)
        if commands:
            print(f"    Found {len(commands)} command(s):")
            for i, cmd in enumerate(commands, 1):
                print(f"\n    Command {i}:")
                print(f"      Type: {cmd.command_type.value}")
                print(f"      Parameters: {cmd.parameters}")
                print(f"      Priority: {cmd.priority}")
        else:
            print("    No commands parsed (parser returned None)")
    except Exception as e:
        print(f"    ERROR: Parsing failed: {e}")
        return
    
    print(f"\n{'='*70}\n")


def main():
    """Main function to test audio files."""
    audio_samples_dir = Path(__file__).parent.parent / "tests" / "pi" / "audio_samples"
    
    if len(sys.argv) > 1:
        audio_files = [Path(sys.argv[1])]
    else:
        audio_files = [
            audio_samples_dir / "single_command.wav",
            audio_samples_dir / "sequence.wav",
            audio_samples_dir / "with_modifier.wav",
        ]
    
    print("Voice Rover Audio Test Script")
    print("=" * 70)
    print("\nThis script demonstrates:")
    print("  1. Audio file → Whisper transcription")
    print("  2. Transcribed text → Command parser")
    print("  3. Parsed commands with parameters")
    
    transcriber = WhisperTranscriber()
    print(f"\nLoading Whisper model ({transcriber.model_size})...")
    print("(This may take a moment on first run - model will be downloaded)")
    transcriber.load_model()
    print("Model loaded!\n")
    
    for audio_file in audio_files:
        if not audio_file.exists():
            print(f"\n⚠️  Audio file not found: {audio_file}")
            print(f"   Skipping...")
            continue
        
        test_audio_file(str(audio_file))
    
    transcriber.unload_model()
    print("\n✅ Testing complete!")


if __name__ == "__main__":
    main()
