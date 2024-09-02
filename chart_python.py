import numpy as np
import matplotlib.pyplot as plt
from collections import deque
import time

# Parameters
X = 100  # Number of last points to display on the chart
mu = 0   # Mean of the normal distribution
sigma = 1  # Standard deviation of the normal distribution
power_exp = 5  # Exponent for the power-law distribution
update_interval = 0.1  # Time between updates in seconds

# Data storage for both distributions
normal_data_stream = deque(maxlen=X)
power_law_data_stream = deque(maxlen=X)

# Initialize plot
plt.ion()  # Interactive mode on
fig, ax = plt.subplots()
normal_line, = ax.plot([], [], lw=2, label='Normal Distribution', color='blue')
power_law_line, = ax.plot([], [], lw=2, label='Power-Law Distribution', color='red')
ax.set_xlim(0, X)
ax.set_ylim(-5, 5)
plt.title("Live Stream: Normal vs Power-Law Distribution")
plt.legend()

def update_chart():
    ax.set_xlim(0, len(normal_data_stream))
    normal_line.set_data(range(len(normal_data_stream)), normal_data_stream)
    power_law_line.set_data(range(len(power_law_data_stream)), power_law_data_stream)
    plt.draw()
    plt.pause(0.01)

def is_plot_closed():
    return not plt.fignum_exists(fig.number)

# Infinite data stream loop
try:
    while True:
        if is_plot_closed():
            print("Plot window closed. Exiting...")
            break
        
        # Generate random data points
        new_normal_data = np.random.normal(mu, sigma)
        new_power_law_data = np.random.power(power_exp) - 0.5  # Shifted for better visualization
        
        # Append the new data points to the respective streams
        normal_data_stream.append(new_normal_data)
        power_law_data_stream.append(new_power_law_data)
        
        # Update the chart with the latest data
        update_chart()
        
        # Sleep for a short interval to simulate streaming
        time.sleep(update_interval)
        
except KeyboardInterrupt:
    print("Script interrupted. Exiting...")

finally:
    plt.ioff()  # Turn off interactive mode
    plt.close(fig)  # Ensure the plot window is closed
