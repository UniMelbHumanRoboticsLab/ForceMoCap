import os, sys, math, time
import numpy as np
from PyQt5 import QtWidgets, QtCore
import pyqtgraph.opengl as gl
from scipy.spatial.transform import Rotation as R

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from mo_cap.hand_ss.hand_ss_server import SSHandClient

class FullRotateGLViewWidget(gl.GLViewWidget):
    def orbit(self, azim, elev):
        """
        Override the default orbit so elevation is never clamped.
        `azim` and `elev` are in degrees, passed in by the
        base class’s mouseDragEvent.
        """
        opts = self.opts
        # accumulate azimuth, wrapping 0–360
        opts['azimuth']   = (opts.get('azimuth', 0.0) + azim) % 360
        # accumulate elevation with no clamp
        opts['elevation'] = opts.get('elevation', 0.0) + elev
        # trigger a redraw
        self.update()

class SS_SingleHand(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.resize(600, 600)
        layout = QtWidgets.QVBoxLayout(self)
        
        # 3D view
        self.view = FullRotateGLViewWidget()
        self.view.opts['distance'] = 6
        layout.addWidget(self.view)
        
        # ground grid
        grid = gl.GLGridItem()
        grid.rotate(90, 1,0,0)
        self.view.addItem(grid)
        
        """init plots"""
        # scatter plot item for the streaming point
        self.skeletons = []
        # self.finger_index = list(range(0, 12)) + list(range(16, 20))
        for i in range(20):
            if i != 0:
                skeleton = gl.GLLinePlotItem(pos=np.vstack([np.array([[0,0,0]]), np.array([[0.5,0.5,0.5]])]), color=(0,0,1,1), width=3, antialias=True)
                self.skeletons.append(skeleton)
                self.view.addItem(skeleton)

        self.distals = {}
        self.bv = np.eye(3) * 0.1  # 3 basis vectors
        for i in [0,4,7,11,15,19]:
            distal = gl.GLScatterPlotItem(
                pos=np.array([[0,0,0]]), size=12, color=(0,1,0,1)
            )
            self.view.addItem(distal)
            # scatter plot for streaming orientation
            # draw triad axes of length .5
            rot = R.from_quat([0,0,0,1]).as_matrix()
            axes = []
            for j, col in enumerate([(1,0,0,1),(0,1,0,1),(0,0,1,1)]):
                v = rot @ self.bv[:,j]     # transform axis
                pts = np.vstack([np.array([[0,0,0]]), np.array([[0,0,0]])+v])
                plt = gl.GLLinePlotItem(pos=pts, color=col, width=3, antialias=True)
                axes.append(plt)
                self.view.addItem(plt)
            self.distals[i] = {"pos":distal,"rot":axes}
        
        """init servers"""
        self.SS = SSHandClient('127.0.0.1',9004)
        
        # timer to update the point
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_skeleton)
        self.timer.start(0)

    def update_skeleton(self):
        fingers_data,print_text = self.SS.return_finger_data()
        
        if print_text is not None:
            print(print_text)

            # draw draw bone and skeleton
            for idx in range(20):
                bone = fingers_data.iloc[idx]
                pos = bone['T_global'][:3,3]/10
                if idx in [0,4,7,11,15,19]:
                    rot = bone['T_global'][:3,:3]
                    self.distals[idx]['pos'].setData(pos=pos)
                    for i, col in enumerate([(1,0,0,1),(0,1,0,1),(0,0,1,1)]):
                        v = rot @ self.bv[:,i]     # transform axis
                        pts = np.vstack([pos, pos+v])
                        self.distals[idx]['rot'][i].setData(pos=pts)
                if bone['parent'] != -1:
                    self.skeletons[idx-1].setData(pos=np.vstack([pos, fingers_data.loc[bone['parent'],'T_global'][:3,3]/10]))
        else:
            pass