# Closed-loop water tank with PLC-style control

A simulated tank controlled by a PLC-style loop, used to study how a spoofed sensor can cause unsafe operation.

## Model
Tank: dh/dt = (Q_in - c*sqrt(h)) / A, solved with an Euler step (dt = 0.1 s).
Controller: pump ON below 1.5, OFF above 2.5 (hysteresis), scanned every 0.1 s.
Parameters: A = 1, c = 0.2, Q_in = 0.5 when the pump is ON.

## Experiments
1. Normal operation
2. Spoofed sensor: measured level = true level - 1.0 between 15 s and 45 s
3. Single threshold vs two-threshold hysteresis

## Results
- Spoofed run: the PLC saw normal cycling, but the true level peaked near 3.5, 1.0 above the 2.5 switch-off threshold. The model has no overflow limit, so "unsafe" here means leaving the designed operating band.
- Simulation: 60 s, starting level 2 m, level in metres, time in seconds.
- Single threshold: pump ON below 2.0 m, OFF above 2.0 m; 300 switches in 60 s, versus about 14 with the two-threshold band (1.5 / 2.5).

## How to run
pip install numpy matplotlib
python closed_loop_tank.py              # experiments 1 and 2
python single_threshold_experiment.py   # experiment 3
Figures are saved to figures/.