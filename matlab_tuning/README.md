# MATLAB PID Tuning Scripts for Voice Rover

These scripts help you tune the balance controller PID gains (Kp, Ki, Kd) for stable, responsive performance.

## Scripts

### 1. `step_response.m` - Primary Tuning Tool
**Purpose:** Tune Kp, Ki, Kd using simulated step response

**When to use:** Before hardware testing, to get initial gain estimates

**What it shows:**
- Rise time (speed)
- Overshoot (stability margin)
- Settling time (convergence)
- Oscillations (damping)

**How to use:**
1. Open `step_response.m`
2. Adjust Kp, Ki, Kd values at the top
3. Run script
4. Look at step response plot and metrics
5. Follow the tuning guidelines printed in console

**Tuning process:**
- Start: Kp=40, Ki=0, Kd=0
- Increase Kp until oscillation, then back off to 70%
- Add Kd to dampen (start with Kp/10)
- Add Ki last for steady-state error (start with Kp/100)

---

### 2. `pole_sweep.m` - Stability Analysis
**Purpose:** Visualize how gains affect stability

**When to use:** To understand stability margins and find safe operating ranges

**What it shows:**
- Pole locations (left = stable, right = unstable)
- Stability boundary (where system goes unstable)
- Damping ratio vs gain

**How to use:**
1. Open `pole_sweep.m`
2. Set `gain_to_sweep` to 'Kp', 'Ki', or 'Kd'
3. Set the other two gains to your current values
4. Run script
5. See stability boundary and recommended max gain

**What to look for:**
- Poles in left half-plane = stable
- Poles near imaginary axis = oscillatory
- Use 70% of stability boundary for safety margin

---

### 3. `log_analysis.m` - Real Data Analysis ⭐ **MOST IMPORTANT**
**Purpose:** Tune using actual rover data (use this once hardware works!)

**When to use:** After initial balancing works, to fine-tune performance

**What it analyzes:**
- Motor saturation (hitting ±255 limits)
- Oscillation frequency
- Recovery time after disturbances
- Steady-state error

**How to use:**

#### Step 1: Add logging to ESP32
Add to `esp32/src/main.cpp` inside the balance loop (after motor output calculation):

```cpp
// Log data for MATLAB analysis
Serial.print(millis()); Serial.print(",");
Serial.print(angle); Serial.print(",");
Serial.print(angular_velocity); Serial.print(",");
Serial.print(motorOutput); Serial.print(",");
Serial.print(balanceController.getVelocitySetpoint()); Serial.print(",");
Serial.print(balanceController.getRotationSetpoint()); Serial.println();
```

#### Step 2: Collect data
```bash
cd esp32
pio device monitor > rover_log.csv
# Let rover balance for 10-30 seconds
# Gently push it to create disturbances
# Press Ctrl+C to stop
```

#### Step 3: Clean CSV (remove non-data lines)
```bash
# Remove header lines and keep only numeric data
grep "^[0-9]" rover_log.csv > rover_log_clean.csv
mv rover_log_clean.csv rover_log.csv
```

#### Step 4: Analyze in MATLAB
```matlab
log_analysis
```

**What the script tells you:**
- ⚠ High saturation → Reduce Ki or increase INTEGRAL_LIMIT
- ⚠ High-frequency oscillations → Increase Kd
- ⚠ Slow recovery → Increase Kp
- ⚠ Steady-state error → Increase Ki

---

## Quick Start Guide

### Phase 1: Simulation (Before Hardware)
```matlab
% 1. Get initial estimates
step_response  % Adjust gains, run until response looks good

% 2. Check stability margins
pole_sweep  % Verify you're not too close to instability
```

### Phase 2: Hardware Tuning (With Rover)
```matlab
% 1. Collect real data (see instructions above)

% 2. Analyze and iterate
log_analysis  % Follow recommendations, adjust gains, repeat
```

---

## Typical Good Values

Based on the default config (may need adjustment for your hardware):
- **Kp:** 30-50 (start with 40)
- **Ki:** 0.2-1.0 (start with 0.5)
- **Kd:** 1.5-3.0 (start with 2.0)

---

## Troubleshooting

### Rover falls immediately
- Reduce Kp by 50%
- Check motor directions (see CLAUDE.md)
- Verify IMU orientation (X-axis forward)

### Oscillates but doesn't fall
- Increase Kd (try 2x current value)
- Reduce Kp slightly

### Slow to recover from pushes
- Increase Kp (try 1.5x current value)

### Always leans to one side
- Increase Ki (or recalibrate IMU)
- Check for mechanical issues

### Motors saturate (hit ±255)
- Reduce integral limit in `config.h`
- Reduce Ki gain

---

## Further Reading

- **Inverted Pendulum Control:** Standard robotics control problem
- **PID Tuning:** Ziegler-Nichols, Cohen-Coon methods
- **MATLAB Control Toolbox:** `step()`, `feedback()`, `pid()` documentation

---

## Notes

- All scripts use simplified linearized model (good enough for initial tuning)
- Real hardware will differ - use `log_analysis.m` for final tuning
- Save working gain values in `config.h` once tuned
- Document any hardware-specific adjustments in project notes
