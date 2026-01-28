% log_analysis.m
% Purpose: Analyze real rover data to tune PID gains
% This is THE MOST PRACTICAL script - use after hardware works
%
% What to look for:
%   - Motor saturation (output hitting ±255)
%   - Oscillations (too much Kp or not enough Kd)
%   - Slow recovery (not enough Kp)
%   - Steady-state error (need more Ki)
%
% How to use:
%   1. Add logging to ESP32 main.cpp (see instructions below)
%   2. Run rover, save serial output to CSV file
%   3. Load CSV here and analyze

clear; close all; clc;

%% Instructions for Data Collection
fprintf('=== Data Collection Instructions ===\n');
fprintf('Add this to ESP32 main.cpp inside the balance loop:\n\n');
fprintf('  Serial.print(millis()); Serial.print(\",\");\n');
fprintf('  Serial.print(angle); Serial.print(\",\");\n');
fprintf('  Serial.print(angular_velocity); Serial.print(\",\");\n');
fprintf('  Serial.print(motorOutput); Serial.print(\",\");\n');
fprintf('  Serial.print(velocity_setpoint); Serial.print(\",\");\n');
fprintf('  Serial.print(rotation_setpoint); Serial.println();\n\n');
fprintf('Then: pio device monitor > log.csv\n');
fprintf('Run rover for 10-30 seconds, then Ctrl+C\n\n');

%% Load Data
% Specify your log file path
log_file = 'rover_log.csv';

if ~exist(log_file, 'file')
    fprintf('ERROR: Log file not found: %s\n', log_file);
    fprintf('Creating sample data for demonstration...\n\n');
    
    % Generate sample data (replace with real data)
    t = (0:0.01:10)';
    angle = 5*sin(2*pi*0.5*t) .* exp(-0.2*t) + randn(size(t))*0.5;
    angular_velocity = gradient(angle) / 0.01;
    motor_output = -40*angle - 2*angular_velocity + randn(size(t))*10;
    velocity_setpoint = zeros(size(t));
    rotation_setpoint = zeros(size(t));
    
    % Add a disturbance at t=5s
    disturbance_idx = find(t >= 5, 1);
    angle(disturbance_idx:end) = angle(disturbance_idx:end) + 10*exp(-0.5*(t(disturbance_idx:end)-5));
    
    data = [t*1000, angle, angular_velocity, motor_output, velocity_setpoint, rotation_setpoint];
else
    % Load real data from CSV
    data = readmatrix(log_file);
    fprintf('Loaded %d samples from %s\n\n', size(data,1), log_file);
end

% Parse columns
time_ms = data(:,1);
angle = data(:,2);
angular_velocity = data(:,3);
motor_output = data(:,4);
velocity_setpoint = data(:,5);
rotation_setpoint = data(:,6);

% Convert time to seconds
time = (time_ms - time_ms(1)) / 1000;

%% Plot 1: Angle and Motor Output
figure(1);
subplot(3,1,1);
plot(time, angle, 'b-', 'LineWidth', 1.5);
hold on;
yline(40, 'r--', 'LineWidth', 1, 'DisplayName', 'Fall Threshold');
yline(-40, 'r--', 'LineWidth', 1);
grid on;
ylabel('Angle (deg)');
title('Balance Controller Performance');
legend('Angle', 'Fall Threshold');

subplot(3,1,2);
plot(time, angular_velocity, 'g-', 'LineWidth', 1.5);
grid on;
ylabel('Angular Velocity (deg/s)');

subplot(3,1,3);
plot(time, motor_output, 'r-', 'LineWidth', 1.5);
hold on;
yline(255, 'k--', 'LineWidth', 1, 'DisplayName', 'Saturation');
yline(-255, 'k--', 'LineWidth', 1);
grid on;
ylabel('Motor Output');
xlabel('Time (s)');
legend('Motor Command', 'Saturation Limits');

%% Analysis: Saturation
saturation_pct = sum(abs(motor_output) >= 255) / length(motor_output) * 100;
fprintf('=== Saturation Analysis ===\n');
fprintf('Motor saturated %.1f%% of the time\n', saturation_pct);
if saturation_pct > 10
    fprintf('⚠ WARNING: High saturation! Reduce Ki or increase integral limit\n');
elseif saturation_pct > 1
    fprintf('ⓘ Moderate saturation - acceptable for aggressive tuning\n');
else
    fprintf('✓ Low saturation - good headroom\n');
end
fprintf('\n');

%% Analysis: Oscillations
% Detect oscillations using FFT
Fs = 100;  % Sample rate (Hz)
L = length(angle);
Y = fft(angle);
P2 = abs(Y/L);
P1 = P2(1:L/2+1);
P1(2:end-1) = 2*P1(2:end-1);
f = Fs*(0:(L/2))/L;

figure(2);
subplot(2,1,1);
plot(f, P1);
grid on;
xlabel('Frequency (Hz)');
ylabel('|FFT(angle)|');
title('Frequency Content of Angle');
xlim([0, 10]);

% Find dominant frequency
[peak_mag, peak_idx] = max(P1(2:end));  % Exclude DC
peak_freq = f(peak_idx+1);

fprintf('=== Oscillation Analysis ===\n');
fprintf('Dominant frequency: %.2f Hz\n', peak_freq);
if peak_freq > 5
    fprintf('⚠ High-frequency oscillations detected!\n');
    fprintf('  → Increase Kd (derivative gain)\n');
elseif peak_freq > 2
    fprintf('ⓘ Moderate oscillations - tune Kd\n');
else
    fprintf('✓ Low-frequency response - well damped\n');
end
fprintf('\n');

%% Analysis: Settling Time
% Find disturbances (large angle changes)
angle_change = abs(diff(angle));
disturbances = find(angle_change > 5);

if ~isempty(disturbances)
    fprintf('=== Recovery Analysis ===\n');
    fprintf('Found %d disturbances\n', length(disturbances));
    
    % Analyze first disturbance
    dist_idx = disturbances(1);
    recovery_start = dist_idx;
    
    % Find settling (angle within 5% of final value)
    final_angle = mean(angle(end-100:end));
    settling_threshold = abs(final_angle) + 0.05 * max(abs(angle));
    
    settled_idx = find(abs(angle(recovery_start:end)) < settling_threshold, 1) + recovery_start;
    if ~isempty(settled_idx)
        settling_time = time(settled_idx) - time(recovery_start);
        fprintf('Settling time: %.2f seconds\n', settling_time);
        
        if settling_time > 2
            fprintf('⚠ Slow recovery - increase Kp\n');
        elseif settling_time > 1
            fprintf('ⓘ Moderate recovery speed\n');
        else
            fprintf('✓ Fast recovery\n');
        end
    end
end
fprintf('\n');

%% Analysis: Steady-State Error
steady_state = angle(end-100:end);
steady_state_error = mean(steady_state);
steady_state_std = std(steady_state);

fprintf('=== Steady-State Analysis ===\n');
fprintf('Mean angle: %.2f degrees\n', steady_state_error);
fprintf('Std dev:    %.2f degrees\n', steady_state_std);

if abs(steady_state_error) > 2
    fprintf('⚠ Large steady-state error - increase Ki\n');
elseif abs(steady_state_error) > 0.5
    fprintf('ⓘ Small steady-state error - Ki may help\n');
else
    fprintf('✓ Negligible steady-state error\n');
end
fprintf('\n');

%% Plot 2: Phase Portrait (angle vs angular velocity)
figure(3);
plot(angle, angular_velocity, 'b-', 'LineWidth', 1);
hold on;
plot(angle(1), angular_velocity(1), 'go', 'MarkerSize', 10, 'LineWidth', 2);
plot(angle(end), angular_velocity(end), 'rx', 'MarkerSize', 10, 'LineWidth', 2);
grid on;
xlabel('Angle (deg)');
ylabel('Angular Velocity (deg/s)');
title('Phase Portrait');
legend('Trajectory', 'Start', 'End');

%% Tuning Recommendations
fprintf('=== Tuning Recommendations ===\n');
fprintf('Based on the analysis above:\n\n');

if saturation_pct > 10
    fprintf('1. Reduce Ki (currently causing saturation)\n');
end
if peak_freq > 5
    fprintf('2. Increase Kd to dampen oscillations\n');
end
if exist('settling_time', 'var') && settling_time > 2
    fprintf('3. Increase Kp for faster response\n');
end
if abs(steady_state_error) > 2
    fprintf('4. Increase Ki to eliminate steady-state error\n');
end

fprintf('\nNext steps:\n');
fprintf('1. Adjust gains based on recommendations\n');
fprintf('2. Re-run hardware test\n');
fprintf('3. Collect new log and re-analyze\n');
