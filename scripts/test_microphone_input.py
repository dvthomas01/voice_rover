#!/usr/bin/env python3
"""Test script to verify microphone is receiving audio input.

This script helps diagnose microphone issues by:
1. Listing available audio devices
2. Testing audio capture
3. Showing audio levels

Usage:
    python scripts/test_microphone_input.py
"""

import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pi.audio_input.microphone import MicrophoneInterface
from pi.config import SAMPLE_RATE, AUDIO_CHANNELS
import pyaudio
import time


def list_audio_devices():
    """List all available audio input devices."""
    print("=" * 70)
    print("AVAILABLE AUDIO INPUT DEVICES")
    print("=" * 70)
    
    audio = pyaudio.PyAudio()
    
    try:
        default_device = audio.get_default_input_device_info()
        print(f"\nDefault input device:")
        print(f"  Index: {default_device['index']}")
        print(f"  Name: {default_device['name']}")
        print(f"  Channels: {default_device['maxInputChannels']}")
        print(f"  Sample Rate: {default_device['defaultSampleRate']}")
    except OSError:
        print("\n⚠️  No default input device found")
    
    print(f"\nAll input devices:")
    device_count = audio.get_device_count()
    input_devices = []
    
    for i in range(device_count):
        try:
            device_info = audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                input_devices.append((i, device_info))
                marker = " (DEFAULT)" if device_info['index'] == default_device['index'] else ""
                usb_marker = " [USB]" if 'usb' in device_info['name'].lower() or 'samson' in device_info['name'].lower() else ""
                print(f"  [{i}] {device_info['name']}{marker}{usb_marker}")
                print(f"      Channels: {device_info['maxInputChannels']}, "
                      f"Sample Rate: {device_info['defaultSampleRate']}")
        except OSError:
            continue
    
    audio.terminate()
    
    return input_devices, default_device['index'] if 'default_device' in locals() else None


def test_audio_capture(duration=3.0):
    """Test audio capture and show audio levels."""
    print("\n" + "=" * 70)
    print("AUDIO CAPTURE TEST")
    print("=" * 70)
    
    print(f"\n🎤 Starting microphone test...")
    print(f"   Duration: {duration} seconds")
    print(f"   Sample rate: {SAMPLE_RATE}Hz")
    print(f"   Channels: {AUDIO_CHANNELS}")
    
    microphone = MicrophoneInterface(SAMPLE_RATE, AUDIO_CHANNELS)
    
    try:
        microphone.start()
        print("✅ Microphone started")
        
        if microphone._selected_device_index is not None:
            device_info = microphone._audio.get_device_info_by_index(microphone._selected_device_index)
            print(f"   Using device: {device_info['name']} (index {microphone._selected_device_index})")
        
        print(f"\n🎙️  Speak into your microphone for {duration} seconds...")
        print(f"   (You should see audio levels below)")
        
        # Capture audio
        audio_data = microphone.capture_audio(duration)
        
        if len(audio_data) == 0:
            print("\n❌ ERROR: No audio data captured!")
            print("   Possible issues:")
            print("   - Microphone not connected")
            print("   - Microphone permissions denied")
            print("   - Wrong device selected")
            return False
        
        # Analyze audio
        max_amplitude = np.max(np.abs(audio_data))
        rms_level = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
        zero_crossings = np.sum(np.diff(np.sign(audio_data)) != 0)
        
        print(f"\n✅ Audio captured successfully!")
        print(f"   Samples captured: {len(audio_data)}")
        print(f"   Duration: {len(audio_data) / SAMPLE_RATE:.2f} seconds")
        print(f"   Max amplitude: {max_amplitude} (out of 32767)")
        print(f"   RMS level: {rms_level:.1f}")
        print(f"   Zero crossings: {zero_crossings}")
        
        # Audio level indicator
        level_percent = (max_amplitude / 32767) * 100
        print(f"\n   Audio level: {'█' * int(level_percent / 5)} {level_percent:.1f}%")
        
        if max_amplitude < 100:
            print(f"\n⚠️  WARNING: Very low audio levels detected!")
            print(f"   - Check microphone is working")
            print(f"   - Check microphone volume/gain")
            print(f"   - Speak louder or closer to microphone")
            return False
        elif max_amplitude < 1000:
            print(f"\n⚠️  WARNING: Low audio levels detected")
            print(f"   - You may need to speak louder")
            print(f"   - Check microphone gain settings")
        else:
            print(f"\n✅ Audio levels look good!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        microphone.stop()
        print("\n✅ Microphone stopped")


def test_chunk_reading():
    """Test reading audio chunks (for wake word detection)."""
    print("\n" + "=" * 70)
    print("AUDIO CHUNK READING TEST")
    print("=" * 70)
    
    print(f"\n🎤 Testing chunk reading (used by wake word detector)...")
    
    microphone = MicrophoneInterface(SAMPLE_RATE, AUDIO_CHANNELS)
    
    try:
        microphone.start()
        print("✅ Microphone started")
        
        print(f"\n🎙️  Reading 5 audio chunks...")
        print(f"   (Speak into microphone)")
        
        chunks_received = 0
        chunks_with_audio = 0
        
        for i in range(5):
            chunk = microphone.get_audio_chunk()
            if chunk is not None:
                chunks_received += 1
                max_amp = np.max(np.abs(chunk))
                if max_amp > 100:
                    chunks_with_audio += 1
                print(f"   Chunk {i+1}: {len(chunk)} samples, max amplitude: {max_amp}")
            else:
                print(f"   Chunk {i+1}: None (no audio)")
            time.sleep(0.5)
        
        print(f"\n✅ Chunk reading test complete")
        print(f"   Chunks received: {chunks_received}/5")
        print(f"   Chunks with audio: {chunks_with_audio}/5")
        
        if chunks_received == 0:
            print(f"\n❌ ERROR: No chunks received!")
            return False
        elif chunks_with_audio == 0:
            print(f"\n⚠️  WARNING: Chunks received but no audio detected")
            print(f"   - Speak louder")
            print(f"   - Check microphone is working")
        else:
            print(f"\n✅ Chunk reading working correctly!")
        
        return chunks_received > 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        microphone.stop()


def main():
    """Main test function."""
    print("=" * 70)
    print("MICROPHONE DIAGNOSTIC TEST")
    print("=" * 70)
    print("\nThis script helps diagnose microphone issues.")
    print("It will test if your microphone is working and receiving audio.\n")
    
    # List devices
    input_devices, default_index = list_audio_devices()
    
    if not input_devices:
        print("\n❌ ERROR: No audio input devices found!")
        print("   - Check microphone is connected")
        print("   - Check System Settings > Sound > Input")
        return
    
    # Test audio capture
    capture_ok = test_audio_capture(duration=3.0)
    
    if not capture_ok:
        print("\n" + "=" * 70)
        print("TROUBLESHOOTING")
        print("=" * 70)
        print("\n1. Check microphone permissions:")
        print("   System Settings > Privacy & Security > Microphone")
        print("   Ensure Terminal (or your IDE) has microphone access")
        print("\n2. Test microphone in another app:")
        print("   - QuickTime (Record > New Audio Recording)")
        print("   - System Settings > Sound > Input (see levels)")
        print("\n3. Check microphone is selected:")
        print("   System Settings > Sound > Input")
        print("   Select your microphone")
        print("\n4. Try different device index:")
        print("   Set AUDIO_DEVICE_INDEX in pi/config.py")
        return
    
    # Test chunk reading
    chunk_ok = test_chunk_reading()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if capture_ok and chunk_ok:
        print("\n✅ Microphone is working correctly!")
        print("   If wake word detection still doesn't work:")
        print("   1. Verify PORCUPINE_ACCESS_KEY is set")
        print("   2. Try increasing WAKE_WORD_SENSITIVITY in config.py")
        print("   3. Speak clearly: 'jarvis'")
    else:
        print("\n⚠️  Microphone has issues")
        print("   Fix the issues above before testing wake word detection")


if __name__ == "__main__":
    main()
