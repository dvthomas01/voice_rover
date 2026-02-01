#!/usr/bin/env python3
"""
Analyze balance tuning data captured from ESP32.

This script loads the CSV data and generates plots to help tune PID gains.

Usage:
    python analyze_balance_data.py balance_data.csv
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def analyze_data(csv_file):
    """Load and analyze balance data."""
    
    print(f"Loading data from '{csv_file}'...")
    
    try:
        # Load CSV
        df = pd.read_csv(csv_file)
        
        print(f"✓ Loaded {len(df)} samples")
        print(f"\nColumns: {list(df.columns)}")
        print(f"\nData summary:")
        print(df.describe())
        
        # Convert timestamp to seconds
        df['time_s'] = (df['timestamp_ms'] - df['timestamp_ms'].iloc[0]) / 1000.0
        
        # Create plots
        fig, axes = plt.subplots(4, 1, figsize=(12, 10))
        fig.suptitle('Balance Controller Analysis', fontsize=16)
        
        # Plot 1: Angle over time
        ax = axes[0]
        ax.plot(df['time_s'], df['angle'], 'b-', linewidth=1, label='Filtered angle')
        ax.plot(df['time_s'], df['accel_angle'], 'r-', alpha=0.3, linewidth=0.5, label='Accel angle')
        ax.axhline(0, color='k', linestyle='--', alpha=0.3)
        ax.set_ylabel('Angle (degrees)')
        ax.set_title('Tilt Angle vs Time')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Plot 2: Gyro rate
        ax = axes[1]
        ax.plot(df['time_s'], df['gyro_rate'], 'g-', linewidth=1)
        ax.axhline(0, color='k', linestyle='--', alpha=0.3)
        ax.set_ylabel('Gyro Rate (deg/s)')
        ax.set_title('Angular Velocity')
        ax.grid(True, alpha=0.3)
        
        # Plot 3: Error and derivative
        ax = axes[2]
        ax.plot(df['time_s'], df['error'], 'r-', linewidth=1, label='Error')
        ax.plot(df['time_s'], df['derror'], 'orange', linewidth=1, alpha=0.7, label='D(error)')
        ax.axhline(0, color='k', linestyle='--', alpha=0.3)
        ax.set_ylabel('Error (degrees)')
        ax.set_title('Control Error and Derivative')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Plot 4: Motor PWM
        ax = axes[3]
        ax.plot(df['time_s'], df['pwm'], 'm-', linewidth=1)
        ax.axhline(255, color='r', linestyle='--', alpha=0.3, label='PWM limit')
        ax.axhline(-255, color='r', linestyle='--', alpha=0.3)
        ax.axhline(0, color='k', linestyle='--', alpha=0.3)
        ax.set_ylabel('PWM Value')
        ax.set_xlabel('Time (seconds)')
        ax.set_title('Motor Control Output')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        plot_file = csv_file.replace('.csv', '_analysis.png')
        plt.savefig(plot_file, dpi=150)
        print(f"\n✓ Saved plot to '{plot_file}'")
        
        # Show plot
        plt.show()
        
        # Calculate statistics
        print("\n" + "=" * 60)
        print("ANALYSIS RESULTS")
        print("=" * 60)
        
        print(f"\nAngle Statistics:")
        print(f"  Mean angle: {df['angle'].mean():.2f}°")
        print(f"  Std dev: {df['angle'].std():.2f}°")
        print(f"  Max deviation: {df['angle'].abs().max():.2f}°")
        
        print(f"\nControl Performance:")
        print(f"  Mean error: {df['error'].mean():.2f}°")
        print(f"  RMS error: {np.sqrt((df['error']**2).mean()):.2f}°")
        print(f"  Max error: {df['error'].abs().max():.2f}°")
        
        print(f"\nMotor Usage:")
        print(f"  PWM range: [{df['pwm'].min():.0f}, {df['pwm'].max():.0f}]")
        print(f"  Mean |PWM|: {df['pwm'].abs().mean():.1f}")
        saturated = (df['pwm'].abs() >= 250).sum()
        print(f"  Saturated samples: {saturated} ({100*saturated/len(df):.1f}%)")
        
        # Tuning recommendations
        print("\n" + "=" * 60)
        print("TUNING RECOMMENDATIONS")
        print("=" * 60)
        
        rms_error = np.sqrt((df['error']**2).mean())
        max_error = df['error'].abs().max()
        saturation_pct = 100 * saturated / len(df)
        oscillations = count_zero_crossings(df['angle'])
        
        if rms_error > 5:
            print("\n⚠ Large RMS error (>5°)")
            print("  → Increase Kp (proportional gain)")
        elif rms_error < 1 and oscillations > len(df) / 200:  # ~0.5 Hz
            print("\n⚠ Oscillating")
            print("  → Decrease Kp or increase Kd")
        
        if saturation_pct > 10:
            print("\n⚠ High PWM saturation (>10%)")
            print("  → Reduce Kp or check for excessive disturbances")
        
        if df['angle'].std() > 3:
            print("\n⚠ High angle variance")
            print("  → Increase Kd (derivative gain) for damping")
        
        if abs(df['angle'].mean()) > 2:
            print(f"\n⚠ Steady-state offset ({df['angle'].mean():.1f}°)")
            print("  → Check IMU calibration or add integral term")
        
        print("\n✓ Analysis complete!")
        
    except FileNotFoundError:
        print(f"❌ File not found: {csv_file}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def count_zero_crossings(signal):
    """Count zero crossings in signal."""
    return ((signal[:-1] * signal[1:]) < 0).sum()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_balance_data.py <csv_file>")
        print("\nExample:")
        print("  python analyze_balance_data.py balance_data.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    analyze_data(csv_file)
