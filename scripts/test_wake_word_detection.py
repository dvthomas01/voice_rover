#!/usr/bin/env python3
"""Test script for wake word detection.

This script tests wake word detection with real-time microphone input.
Note: This requires a microphone and the PORCUPINE_ACCESS_KEY to be set.

Usage:
    python scripts/test_wake_word_detection.py
"""

import sys
import os
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pi.audio_input.microphone import MicrophoneInterface
from pi.wake_word.detector import WakeWordDetector
from pi.config import SAMPLE_RATE, AUDIO_CHANNELS, WAKE_WORD


def test_wake_word_detection():
    """Test wake word detection with real microphone.
    
    Works with any microphone including MacBook built-in mic.
    """
    print("=" * 70)
    print("WAKE WORD DETECTION TEST")
    print("=" * 70)
    
    # Check access key
    access_key = os.getenv('PORCUPINE_ACCESS_KEY', '')
    if not access_key:
        print("\n❌ Error: PORCUPINE_ACCESS_KEY not set")
        print("   Get a free key from: https://console.picovoice.ai/")
        print("\n   To set for current session:")
        print("   export PORCUPINE_ACCESS_KEY='your-key-here'")
        print("\n   To set permanently (fix quote issue):")
        print("   echo 'export PORCUPINE_ACCESS_KEY=\"your-key-here\"' >> ~/.zshrc")
        print("   source ~/.zshrc")
        print("\n   Or manually edit ~/.zshrc and add:")
        print("   export PORCUPINE_ACCESS_KEY=\"your-key-here\"")
        return False
    
    print(f"\n✅ Porcupine access key found")
    print(f"   Key (first 20 chars): {access_key[:20]}...")
    print(f"   Wake word: '{WAKE_WORD}'")
    print(f"   Sensitivity: 0.5 (adjust in config.py if needed)")
    print(f"\n🎤 Starting microphone...")
    print(f"   Sample rate: {SAMPLE_RATE}Hz")
    print(f"   Channels: {AUDIO_CHANNELS} (mono)")
    
    # Initialize components
    microphone = MicrophoneInterface(SAMPLE_RATE, AUDIO_CHANNELS)
    wake_word = WakeWordDetector()
    
    detection_count = 0
    chunk_count = 0
    
    def on_wake_word_detected():
        nonlocal detection_count
        detection_count += 1
        print(f"\n🔔 WAKE WORD DETECTED! (#{detection_count})")
        print(f"   Time: {time.strftime('%H:%M:%S')}")
    
    try:
        # Start microphone
        microphone.start()
        print("✅ Microphone started")
        if microphone._selected_device_index is not None:
            import pyaudio
            device_info = microphone._audio.get_device_info_by_index(microphone._selected_device_index)
            print(f"   Device: {device_info['name']} (index {microphone._selected_device_index})")
        
        # Initialize wake word detector
        wake_word.set_callback(on_wake_word_detected)
        wake_word.initialize()
        
        if wake_word._detector is None:
            print("\n❌ Failed to initialize wake word detector")
            print("   Check that PORCUPINE_ACCESS_KEY is valid")
            return False
        
        print(f"✅ Wake word detector initialized")
        print(f"   Frame length: {wake_word._frame_length} samples")
        print(f"\n🎙️  Listening for wake word '{WAKE_WORD}'...")
        print(f"   Say '{WAKE_WORD}' clearly and wait for detection")
        print(f"   Make sure you're speaking clearly and at normal volume")
        print(f"   Press Ctrl+C to stop\n")
        
        # Listen for wake word
        last_status_time = time.time()
        while True:
            chunk = microphone.get_audio_chunk()
            if chunk is not None:
                chunk_count += 1
                wake_word.process_audio(chunk, sample_rate=microphone.sample_rate)
                
                # Print status every 5 seconds
                if time.time() - last_status_time >= 5.0:
                    print(f"   [Status] Processing audio... ({chunk_count} chunks processed, {detection_count} detections)")
                    last_status_time = time.time()
            else:
                print("⚠️  Warning: No audio chunk received")
                time.sleep(0.1)
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print(f"\n\n🛑 Stopping...")
        print(f"   Total detections: {detection_count}")
        print(f"   Total chunks processed: {chunk_count}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        wake_word.cleanup()
        microphone.stop()
        print("✅ Cleanup complete")
    
    if detection_count == 0:
        print(f"\n⚠️  No detections. Troubleshooting tips:")
        print(f"   1. Check microphone permissions (System Settings > Privacy > Microphone)")
        print(f"   2. Speak clearly: '{WAKE_WORD}'")
        print(f"   3. Try increasing sensitivity in config.py: WAKE_WORD_SENSITIVITY = 0.7")
        print(f"   4. Check microphone is working: Test with other apps")
        print(f"   5. Verify access key is valid")
    
    return True


if __name__ == "__main__":
    test_wake_word_detection()
