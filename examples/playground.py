# from PySide6 import QtWidgets, QtCore # use 6.9.0
# from PySide6.QtCore import QTimer,Qt
# from PySide6.QtGui import QFont
# from vispy import scene
# from vispy.app import use_app
# print(use_app('pyside6'))

# import pyqtgraph as pg # use dev pyqtgraph
# pg.setConfigOptions(antialias=False)     # lines render faster
# pg.setConfigOptions(useOpenGL=True)
# pg.setConfigOptions(useCupy=True)
# pg.setConfigOptions(useNumba=True)
# pg.setConfigOptions(crashWarning=True)
# pg.systemInfo()

# import numpy as np
# p = np.concatenate((np.array([0,"HI"]),np.array([0,0,0])))
# print(p)

import matplotlib.pyplot as plt
import numpy as np

def plot_arc(ax, start, end, center, tool_radius, label, side="left", color="blue"):
    """
    Plot programmed arc and toolpath arc with cutter compensation.
    side: "left" for G41, "right" for G42
    """
    # programmed arc
    theta1 = np.arctan2(start[1]-center[1], start[0]-center[0])
    theta2 = np.arctan2(end[1]-center[1], end[0]-center[0])

    # ensure correct direction CCW (G03)
    if theta2 < theta1:
        theta2 += 2*np.pi

    theta = np.linspace(theta1, theta2, 100)
    arc_x = center[0] + np.cos(theta)*(np.linalg.norm([start[0]-center[0], start[1]-center[1]]))
    arc_y = center[1] + np.sin(theta)*(np.linalg.norm([start[0]-center[0], start[1]-center[1]]))
    ax.plot(arc_x, arc_y, "k--", label="Programmed Path" if label else "")

    # offset arc center depending on G41/G42 (left/right)
    # tangent direction at start
    tangent = np.array([-(start[1]-center[1]), (start[0]-center[0])])
    tangent /= np.linalg.norm(tangent)
    if side == "left":
        offset_dir = np.array([-tangent[1], tangent[0]])  # 90° left
    else:
        offset_dir = np.array([tangent[1], -tangent[0]])  # 90° right

    offset_center = center + offset_dir*tool_radius

    # recompute arc with offset radius
    theta_off1 = np.arctan2(start[1]-offset_center[1], start[0]-offset_center[0])
    theta_off2 = np.arctan2(end[1]-offset_center[1], end[0]-offset_center[0])
    if theta_off2 < theta_off1:
        theta_off2 += 2*np.pi
    theta_off = np.linspace(theta_off1, theta_off2, 100)
    arc_off_x = offset_center[0] + np.cos(theta_off)*np.linalg.norm([start[0]-offset_center[0], start[1]-offset_center[1]])
    arc_off_y = offset_center[1] + np.sin(theta_off)*np.linalg.norm([start[0]-offset_center[0], start[1]-offset_center[1]])
    ax.plot(arc_off_x, arc_off_y, color, label=f"Toolpath ({'G41' if side=='left' else 'G42'})" if label else "")

# Example: from your N050 move
start = np.array([1.0, 2.0])
end = np.array([1.5, 2.5])
center = np.array([1.0, 2.5])
tool_radius = 0.2

fig, ax = plt.subplots(figsize=(6,6))
plot_arc(ax, start, end, center, tool_radius, label=True, side="left", color="blue")  # G41
plot_arc(ax, start, end, center, tool_radius, label=False, side="right", color="red") # G42

# markers for clarity
ax.plot([start[0], end[0]], [start[1], end[1]], "ko", label="Start/End")
ax.plot(center[0], center[1], "kx", label="Arc Center")

ax.set_aspect("equal", "box")
ax.legend()
ax.set_title("Effect of G41 vs G42 on Arc Toolpath")
plt.xlabel("X")
plt.ylabel("Y")
plt.grid(True)
plt.show()