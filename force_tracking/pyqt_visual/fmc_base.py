import sys
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph.opengl as gl
from spatialmath import SE3,SO3

class FullRotateGLViewWidget(gl.GLViewWidget):
    def __init__(self, *args, **kwargs):
        """
        Basic widget for displaying 3D data
          - Rotation/scale controls
          - Axis/grid display
          - Export options

        ================ ==============================================================
        **Arguments:**
        parent           (QObject, optional): Parent QObject. Defaults to None.
        devicePixelRatio No longer in use. High-DPI displays should automatically
                         detect the correct resolution.
        rotationMethod   (str): Mechanism to drive the rotation method, options are
                         'euler' and 'quaternion'. Defaults to 'euler'.
        ================ ==============================================================
        """
        super().__init__(*args, **kwargs)
        
    def mouseMoveEvent(self, ev):
        lpos = ev.position() if hasattr(ev, 'position') else ev.localPos()
        if not hasattr(self, 'mousePos'):
            self.mousePos = lpos
        diff = lpos - self.mousePos
        self.mousePos = lpos
                
        if ev.buttons() == QtCore.Qt.MouseButton.LeftButton:
            if (ev.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
                self.pan(diff.x(), diff.y(), 0, relative='view')
            else:
                self.orbit(-diff.x(), diff.y())
        elif ev.buttons() == QtCore.Qt.MouseButton.MiddleButton:
            if (ev.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
                self.pan(diff.x(), 0, diff.y(), relative='view')
            else:
                self.pan(diff.x(), diff.y(), 0, relative='view')
        
        self.update()

class FMC_Base(QtWidgets.QWidget):
    def __init__(self,freq=100):
        super().__init__()
        self.resize(1500, 1000)
        
        self.layout = QtWidgets.QVBoxLayout(self)

        self.fps_label = QtWidgets.QLabel("FPS: 0.00")
        self.fps_label.setFixedSize(600,20)
        self.layout.addWidget(self.fps_label)

        # 3D view
        self.view = FullRotateGLViewWidget(rotationMethod='quaternion')
        self.view.opts['distance'] = 10
        self.view.opts['fov'] = 90
        self.triaxis_color = [(1,0,0,1),(0,1,0,1),(0,0,1,1)]
        # ground grid
        grid = gl.GLGridItem(size = QtGui.QVector3D(1,1,1))
        grid.setSpacing(0.1, 0.1, 0.1)
        self.view.addItem(grid)
        self.layout.addWidget(self.view)
        # inertial coordinate system
        self.inert_frame = SO3().R
        self.inert_point = np.array([[0,0,0]])
        self.view.addItem(gl.GLScatterPlotItem(pos=self.inert_point, size=12, color=(0,1,1,1)))

        for j, color in enumerate(self.triaxis_color):
            v = self.inert_frame[:,j]     # transform axis
            pts = np.vstack([self.inert_point, self.inert_point+v])
            plt = gl.GLLinePlotItem(pos=pts, color=color, width=3, antialias=True)
            self.view.addItem(plt)

        # timer to update the point
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_env)
        self.timer.start(int(1/freq*1000)) #1000ms - 1Hz

        # Timer and FPS variables
        self.frame_count = 0
        self.fps = 0
        self.elapsed_timer = QtCore.QElapsedTimer() # use the system clock
        self.elapsed_timer.start()
        self.cur_time = self.elapsed_timer.elapsed()
        self.last_time = self.elapsed_timer.elapsed()

    def update_env(self):
        self.frame_count += 1
        self.cur_time = self.elapsed_timer.elapsed()
        # Update FPS every second
        if self.cur_time-self.last_time >= 500:
            self.fps = self.frame_count * 1000 / (self.cur_time-self.last_time)
            self.last_time = self.cur_time
            self.frame_count = 0
        self.fps_label.setText(f"FPS_1: {self.fps:.2f}Hz")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = FMC_Base(freq=75)
    w.setWindowTitle("ForceMoCap")
    w.show()
    sys.exit(app.exec_())
