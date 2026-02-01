#!/usr/bin/env python3
"""List all available audio devices and show which one will be selected.

This script helps verify which microphone is being used by the audio pipeline.
"""

import sounddevice as sd


def main():
    print("=" * 80)
    print("Audio Devices Available on This System")
    print("=" * 80)
    
    devices = sd.query_devices()
    default_input, default_output = sd.default.device
    
    print(f"\nDefault Input Device Index: {default_input}")
    print(f"Default Output Device Index: {default_output}\n")
    
    print("-" * 80)
    print(f"{'ID':<4} {'Name':<40} {'Channels':<12} {'Type'}")
    print("-" * 80)
    
    usb_devices = []
    samson_devices = []
    
    for i, device in enumerate(devices):
        device_name = device['name']
        max_in = device['max_input_channels']
        max_out = device['max_output_channels']
        
        # Determine device type
        device_type = []
        if max_in > 0:
            device_type.append(f"Input ({max_in}ch)")
        if max_out > 0:
            device_type.append(f"Output ({max_out}ch)")
        
        type_str = ", ".join(device_type) if device_type else "None"
        
        # Special markers
        markers = []
        if i == default_input and max_in > 0:
            markers.append("[DEFAULT INPUT]")
        if i == default_output and max_out > 0:
            markers.append("[DEFAULT OUTPUT]")
        
        # Track USB devices
        device_name_lower = device_name.lower()
        if 'usb' in device_name_lower and max_in > 0:
            usb_devices.append((i, device_name))
            markers.append("[USB]")
        if 'samson' in device_name_lower and max_in > 0:
            samson_devices.append((i, device_name))
            markers.append("[SAMSON]")
        if 'go mic' in device_name_lower and max_in > 0:
            markers.append("[GO MIC]")
        
        marker_str = " ".join(markers)
        
        print(f"{i:<4} {device_name:<40} {type_str:<12} {marker_str}")
    
    print("-" * 80)
    
    # Selection logic (mirrors microphone.py)
    print("\n" + "=" * 80)
    print("Device Selection Logic (same as microphone.py)")
    print("=" * 80)
    
    print("\nPriority order:")
    print("  1. Explicitly configured device index (in config.py)")
    print("  2. USB microphone (contains 'usb', 'samson', or 'go mic' in name)")
    print("  3. Default input device")
    
    selected_device = None
    selection_reason = ""
    
    # Check for Go Mic devices (Samson Go Mic, Go Mic Video, etc.)
    go_mic_devices = []
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            device_name_lower = device['name'].lower()
            if 'go mic' in device_name_lower:
                go_mic_devices.append((i, device['name']))
    
    # Check for Samson or USB devices first (priority 2)
    if go_mic_devices:
        selected_device, device_name = go_mic_devices[0]
        selection_reason = "Go Mic USB microphone found"
    elif samson_devices:
        selected_device, device_name = samson_devices[0]
        selection_reason = "Samson USB microphone found"
    elif usb_devices:
        selected_device, device_name = usb_devices[0]
        selection_reason = "USB microphone found"
    elif default_input is not None:
        selected_device = default_input
        device_name = devices[default_input]['name']
        selection_reason = "No USB mic found, using default input"
    
    if selected_device is not None:
        print(f"\n>>> SELECTED DEVICE <<<")
        print(f"  Index: {selected_device}")
        print(f"  Name: {device_name}")
        print(f"  Reason: {selection_reason}")
        print(f"  Channels: {devices[selected_device]['max_input_channels']} input")
        print(f"  Sample Rate: {devices[selected_device]['default_samplerate']} Hz")
    else:
        print("\n>>> NO INPUT DEVICE FOUND <<<")
    
    print("\n" + "=" * 80)
    print("Verification Tips")
    print("=" * 80)
    print("\nTo confirm the Samson mic is being used:")
    print("  1. Run this script WITH Samson plugged in")
    print("     - Should see '[SAMSON]' or '[USB]' marker on Samson device")
    print("     - Should be SELECTED above")
    print()
    print("  2. Run this script WITHOUT Samson plugged in")
    print("     - Should NOT see Samson device in list")
    print("     - Should select default input (likely built-in mic)")
    print()
    print("  3. Check logs when running test_audio_pipeline_sounddevice.py")
    print("     - Look for: 'Using audio device: <name> (index <N>)'")
    print("     - Confirm name matches the device you expect")
    print()


if __name__ == "__main__":
    main()
