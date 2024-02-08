import numpy as np

# Known x and y values
x = np.array([1, 2, 3, 4, 5])
y = np.array([2, 4, 6, 8, 10])

# Fit a linear line to the known data points
model = np.polyfit(x, y, 1)

# New x values for which to extrapolate the y values
new_x = np.array([6, 7])

# Extrapolate the y values for the new x values
new_y = np.polyval(model, new_x)

print(new_y)