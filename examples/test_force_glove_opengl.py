
import sys
import os
from PyQt5 import QtWidgets, QtCore

import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from force_tracking.pyqt_visual.ss_force_serial import SS_Force_Serial

np.set_printoptions(
    precision=2,
    linewidth=np.inf,   
    formatter={'float_kind': lambda x: f"{x:.6f}"}
)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = SS_Force_Serial()
    w.setWindowTitle("Streaming 3D Point")
    w.show()
    sys.exit(app.exec_())
