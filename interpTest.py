import numpy as np
from scipy.interpolate import griddata, RectBivariateSpline
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

x_list = np.array([  10.0,  10.0,   0.0,    0.0])
y_list = np.array([  20.0,  30.0,   30.0,    20.0])
z_list = np.array([103.95, 105.5, 104.85, 104.6])

xi = np.linspace(min(x_list), max(x_list),1000)
yi = np.linspace(min(y_list), max(y_list),1000)

grid_x, grid_y = np.meshgrid(xi, yi, indexing = 'ij')

grid_z1 = griddata((x_list, y_list), z_list, (grid_x, grid_y), method='nearest')
grid_z2 = griddata((x_list, y_list), z_list, (grid_x, grid_y), method='linear')
grid_z3 = griddata((x_list, y_list), z_list, (grid_x, grid_y), method='cubic')

z = RectBivariateSpline(xi, yi, grid_z2, kx=1, ky=1, s=0)
print (z(10.0, 0.0)[0,0]) #return 103.95)))

fig = plt.figure()
ax1 = fig.add_subplot(221, projection='3d')
surf = ax1.plot_surface(grid_x, grid_y, grid_z1)
ax1.set_xlabel(u'X')
ax1.set_ylabel(u'Y')
ax1.set_zlabel(u'Z')

ax2 = fig.add_subplot(222, projection='3d')
surf = ax2.plot_surface(grid_x, grid_y, grid_z2)
ax2.set_xlabel(u'X')
ax2.set_ylabel(u'Y')
ax2.set_zlabel(u'Z')

ax3 = fig.add_subplot(223, projection='3d')
surf = ax3.plot_surface(grid_x, grid_y, grid_z3)
ax3.set_xlabel(u'X')
ax3.set_ylabel(u'Y')
ax3.set_zlabel(u'Z')

plt.show()