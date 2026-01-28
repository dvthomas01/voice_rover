% step_response.m
% Purpose: Tune Kp, Ki, Kd for stability and responsiveness
% Usage: Adjust PID gains and observe step response characteristics
%
% What to look for:
%   - Rise time (speed to reach target)
%   - Overshoot (how much it overshoots)
%   - Settling time (time to stabilize)
%   - Oscillations (indicates too much gain)

clear; close all; clc;

%% Robot Parameters (adjust for your Voice Rover)
% These are estimates - tune based on actual hardware
m = 1.0;        % Mass of robot body (kg)
M = 0.2;        % Mass of wheels (kg)
L = 0.1;        % Distance from wheel axle to center of mass (m)
g = 9.81;       % Gravity (m/s^2)
I = 0.01;       % Moment of inertia (kg*m^2)

%% Linearized Inverted Pendulum Model
% Transfer function from motor torque to tilt angle
% Simplified: angle(s) / torque(s)

% State space or transfer function representation
% For inverted pendulum: d²θ/dt² ≈ (g/L)*θ - (1/(m*L²))*τ
% Linearized around θ=0

% Numerator and denominator for G(s) = angle/torque
num = [1/(m*L^2)];
den = [1, 0, -g/L];

sys = tf(num, den);

% Add actuator dynamics (motor + driver lag, ~20ms)
actuator_lag = tf(1, [0.02, 1]);
plant = sys * actuator_lag;

%% PID Controller Parameters
% START HERE: Tune these values
Kp = 40.0;   % Proportional gain (start with this only, Ki=0, Kd=0)
Ki = 0.5;    % Integral gain (add last, after Kd)
Kd = 2.0;    % Derivative gain (add second, after Kp works)

% Create PID controller
C = pid(Kp, Ki, Kd);

%% Closed-Loop System
% Feedback: angle → PID → motor → plant → angle
closed_loop = feedback(C * plant, 1);

%% Step Response
figure(1);
step(closed_loop);
grid on;
title('Step Response: Tilt Angle Recovery');
xlabel('Time (seconds)');
ylabel('Angle (degrees)');

% Get step response info
info = stepinfo(closed_loop);
fprintf('\n=== Step Response Metrics ===\n');
fprintf('Rise Time:     %.3f s\n', info.RiseTime);
fprintf('Settling Time: %.3f s\n', info.SettlingTime);
fprintf('Overshoot:     %.1f %%\n', info.Overshoot);
fprintf('Peak:          %.3f\n', info.Peak);

%% Stability Check
poles = pole(closed_loop);
fprintf('\n=== Stability Analysis ===\n');
fprintf('Closed-loop poles:\n');
disp(poles);

if all(real(poles) < 0)
    fprintf('✓ System is STABLE (all poles in left half-plane)\n');
else
    fprintf('✗ System is UNSTABLE!\n');
end

%% Tuning Guidelines (printed to console)
fprintf('\n=== Tuning Guidelines ===\n');
fprintf('1. Start with Kp only (Ki=0, Kd=0):\n');
fprintf('   - Increase Kp until oscillation starts\n');
fprintf('   - Back off to 60-70%% of that value\n');
fprintf('\n');
fprintf('2. Add Kd to dampen oscillations:\n');
fprintf('   - Start with Kd = Kp/10\n');
fprintf('   - Increase until overshoot is acceptable (<10%%)\n');
fprintf('\n');
fprintf('3. Add Ki to eliminate steady-state error:\n');
fprintf('   - Start small (Ki = Kp/100)\n');
fprintf('   - Increase slowly - too much causes instability\n');
fprintf('\n');
fprintf('Current gains: Kp=%.1f, Ki=%.2f, Kd=%.1f\n', Kp, Ki, Kd);
