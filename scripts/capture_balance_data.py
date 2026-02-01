#!/usr/bin/env python3
"""
Capture CSV data from ESP32 balance tuning sketch.

This script connects to the ESP32, sends logging commands, and saves
the CSV data to a file for later analysis with MATLAB or Python.

Usage:
    python capture_balance_data.py /dev/ttyUSB0 balance_data.csv 30
    
    Arguments:
        port: Serial port (e.g., /dev/ttyUSB0)
        output_file: CSV filename to save data
        duration: How many seconds to log (default: 30)
"""

import sys
import serial
import time
from datetime import datetime

def capture_data(port, output_file, duration=30):
    """Capture CSV data from ESP32 for specified duration."""
    
    print(f"Connecting to ESP32 on {port}...")
    
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        time.sleep(2)  # Wait for ESP32 to initialize
        
        print("✓ Connected!")
        print("\nSending commands:")
        
        # Send start command
        ser.write(b'S')
        print("  S = Start balance control")
        time.sleep(0.5)
        
        # Send logging command
        ser.write(b'L')
        print("  L = Start CSV logging")
        time.sleep(0.5)
        
        # Read initial header/messages
        print("\nESP32 Output:")
        print("-" * 60)
        
        start_time = time.time()
        csv_started = False
        
        with open(output_file, 'w') as f:
            print(f"\nLogging data for {duration} seconds to '{output_file}'...")
            print("(Keep robot upright!)\n")
            
            lines_logged = 0
            
            while time.time() - start_time < duration:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    # Print comments to console
                    if line.startswith('#'):
                        print(line)
                        continue
                    
                    # Check for CSV header
                    if line.startswith('timestamp_ms'):
                        print(f"✓ CSV header received")
                        csv_started = True
                        f.write(line + '\n')
                        continue
                    
                    # Log CSV data
                    if csv_started and ',' in line:
                        f.write(line + '\n')
                        lines_logged += 1
                        
                        # Print progress every second
                        if lines_logged % 100 == 0:  # ~100Hz logging
                            elapsed = time.time() - start_time
                            print(f"  Logged {lines_logged} samples ({elapsed:.1f}s / {duration}s)")
            
            # Stop logging
            ser.write(b'N')
            print("\n✓ Logging stopped")
            print(f"✓ Saved {lines_logged} samples to '{output_file}'")
            
            # Stop control
            ser.write(b'X')
            print("✓ Balance control stopped")
        
        ser.close()
        
        print("\n" + "=" * 60)
        print("Data capture complete!")
        print("=" * 60)
        print(f"\nData saved to: {output_file}")
        print(f"Samples: {lines_logged}")
        print(f"Duration: {duration}s")
        print(f"\nAnalyze with:")
        print(f"  python analyze_balance_data.py {output_file}")
        print(f"  Or open in MATLAB/Excel")
        
    except serial.SerialException as e:
        print(f"\n❌ Serial error: {e}")
        print("\nTroubleshooting:")
        print("  - Is ESP32 connected?")
        print("  - Check port: ls /dev/ttyUSB* /dev/ttyACM*")
        print("  - Check permissions: sudo usermod -a -G dialout $USER")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        print("Stopping control...")
        ser.write(b'N')  # Stop logging
        ser.write(b'X')  # Stop control
        ser.close()
        print("✓ Stopped safely")
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python capture_balance_data.py <port> <output_file> [duration]")
        print("\nExample:")
        print("  python capture_balance_data.py /dev/ttyUSB0 balance_data.csv 30")
        sys.exit(1)
    
    port = sys.argv[1]
    output_file = sys.argv[2]
    duration = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    
    capture_data(port, output_file, duration)
