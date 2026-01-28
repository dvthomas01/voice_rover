% pole_sweep.m
% Purpose: Visualize how PID gains affect stability
% Shows how close the system is to instability as gains change
%
% What to look for:
%   - Poles crossing imaginary axis = unstable
%   - Poles near imaginary axis = oscillatory
%   - Poles far left = stable but may be overdamped

clear; close all; clc;

%% Robot Parameters (match step_response.m)
m = 1.0;
M = 0.2;
L = 0.1;
g = 9.81;
I = 0.01;

%% Plant Model
num = [1/(m*L^2)];
den = [1, 0, -g/L];
sys = tf(num, den);
actuator_lag = tf(1, [0.02, 1]);
plant = sys * actuator_lag;

%% Sweep Parameters
% Choose which gain to sweep
gain_to_sweep = 'Kp';  % Options: 'Kp', 'Ki', 'Kd'

% Fixed gains (adjust based on your tuning)
Kp_fixed = 40.0;
Ki_fixed = 0.5;
Kd_fixed = 2.0;

% Sweep range
switch gain_to_sweep
    case 'Kp'
        sweep_values = linspace(0, 100, 50);
        Kp_sweep = sweep_values;
        Ki_sweep = Ki_fixed;
        Kd_sweep = Kd_fixed;
        label = 'K_p';
    case 'Ki'
        sweep_values = linspace(0, 5, 50);
        Kp_sweep = Kp_fixed;
        Ki_sweep = sweep_values;
        Kd_sweep = Kd_fixed;
        label = 'K_i';
    case 'Kd'
        sweep_values = linspace(0, 10, 50);
        Kp_sweep = Kp_fixed;
        Ki_sweep = Ki_fixed;
        Kd_sweep = sweep_values;
        label = 'K_d';
end

%% Pole Sweep
figure(1);
hold on; grid on;

colors = jet(length(sweep_values));

for i = 1:length(sweep_values)
    C = pid(Kp_sweep(i), Ki_sweep(i), Kd_sweep(i));
    cl = feedback(C * plant, 1);
    p = pole(cl);
    
    plot(real(p), imag(p), 'o', 'Color', colors(i,:), ...
         'MarkerSize', 6, 'LineWidth', 1.5);
end

% Plot imaginary axis (stability boundary)
yline(0, 'k--', 'LineWidth', 1.5);
xline(0, 'r--', 'LineWidth', 2, 'DisplayName', 'Stability Boundary');

xlabel('Real Part');
ylabel('Imaginary Part');
title(sprintf('Pole Locations vs %s', label));
legend('Location', 'best');

% Add colorbar to show gain values
colormap(jet);
cb = colorbar;
cb.Label.String = sprintf('%s Value', label);
caxis([min(sweep_values), max(sweep_values)]);

% Annotate regions
text(-5, max(ylim)*0.8, 'STABLE', 'FontSize', 14, 'FontWeight', 'bold', 'Color', 'g');
text(0.5, max(ylim)*0.8, 'UNSTABLE', 'FontSize', 14, 'FontWeight', 'bold', 'Color', 'r');

%% Stability Margin Analysis
figure(2);
subplot(2,1,1);
hold on; grid on;

stable_count = zeros(size(sweep_values));
for i = 1:length(sweep_values)
    C = pid(Kp_sweep(i), Ki_sweep(i), Kd_sweep(i));
    cl = feedback(C * plant, 1);
    p = pole(cl);
    stable_count(i) = all(real(p) < 0);
end

plot(sweep_values, stable_count, 'b-', 'LineWidth', 2);
xlabel(sprintf('%s Value', label));
ylabel('Stable (1) / Unstable (0)');
title('Stability vs Gain');
ylim([-0.1, 1.1]);

% Find stability boundary
if any(diff(stable_count) ~= 0)
    boundary_idx = find(diff(stable_count) ~= 0, 1);
    boundary_value = sweep_values(boundary_idx);
    xline(boundary_value, 'r--', 'LineWidth', 2);
    text(boundary_value, 0.5, sprintf('  Boundary: %.2f', boundary_value), ...
         'FontSize', 12, 'Color', 'r');
end

subplot(2,1,2);
hold on; grid on;

% Damping ratio
damping_ratios = zeros(size(sweep_values));
for i = 1:length(sweep_values)
    C = pid(Kp_sweep(i), Ki_sweep(i), Kd_sweep(i));
    cl = feedback(C * plant, 1);
    [wn, zeta] = damp(cl);
    damping_ratios(i) = min(zeta);  % Minimum damping ratio
end

plot(sweep_values, damping_ratios, 'b-', 'LineWidth', 2);
yline(0.707, 'g--', 'LineWidth', 1.5, 'DisplayName', 'Critical Damping');
xlabel(sprintf('%s Value', label));
ylabel('Min Damping Ratio');
title('Damping vs Gain');
legend('Location', 'best');

fprintf('\n=== Pole Sweep Results ===\n');
fprintf('Sweeping: %s from %.2f to %.2f\n', label, min(sweep_values), max(sweep_values));
fprintf('Stable range: %s < %.2f\n', label, boundary_value);
fprintf('\nRecommendation: Use %s ≈ %.2f (70%% of boundary)\n', ...
        label, 0.7 * boundary_value);
