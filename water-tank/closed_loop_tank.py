import numpy as np
import matplotlib.pyplot as plt

A = 1
c = 0.2
dt = 0.1
h = 2.0
LOW = 1.5
HIGH = 2.5
Q_PUMP = 0.5
Q_in = 0
state = False
time = np.arange(0, 60, dt)
results = []

def tank_ode(h, Q_in, c, A):
        safe_h = np.maximum(h, 0)
        rate = ( Q_in - c * np.sqrt(safe_h))/A
        return rate

def plc_scan(level_reading, state):
        if level_reading < LOW:
            state = True
        elif level_reading > HIGH:
            state = False
        return state

def plc_output(state):
        if state:
              Q_in = Q_PUMP
        else:
             Q_in = 0
        return Q_in

for step in range(len(time)):
    measured = h
    if 15.0 <= time[step] <= 45.0:
        measured = measured - 1.0

    results.append([h, measured, int(state)])

    rate = tank_ode(h, Q_in, c, A)
    h = h + rate * dt

    state = plc_scan(measured, state)
    
    Q_in = plc_output(state)
    

results = np.array(results)

fig, (ax, ax2) = plt.subplots(nrows=2, ncols=1, sharex=True)

ax.plot(time, results[:, 0], label='True Height')
ax.plot(time, results[:, 1], label='Measured Height (spoofed)')
ax2.plot(time, results[:, 2], label='State')
ax2.set_xlabel('Time (s)')
ax.legend()
ax2.legend()
ax.axhline(y=LOW, linestyle='--')
ax.axhline(y=HIGH, linestyle='--')
ax.axvspan(15, 45, alpha=0.2)
ax.set_ylabel('Level (m)')
ax2.set_ylabel('Pump (0 = OFF, 1 = ON)')
plt.show()