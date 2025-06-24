from fmc_base import FMC_Base
import os, sys
import numpy as np
from PyQt5 import QtWidgets
import pyqtgraph.opengl as gl
from spatialmath import SO3
from scipy.spatial.transform import Rotation as R

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from mo_cap.vive.openvr_server import OpenVRServer

class FMC_Glove_eval(FMC_Base):
    def __init__(self,freq,num_vive_markers):
        super().__init__(freq=freq)
        self.num_vive_markers = num_vive_markers
        self.init_vive()

    def update_env(self):
        super().update_env() # call to update the frame rate
        self.update_vive()

    def init_vive(self):
        self.vive = OpenVRServer()
        self.inert_vive_rotation = SO3().Rx(90).R
        # Vive frame
        self.marker_list = []
        for i in range(self.num_vive_markers):
            #init vive position plot
            vive_pos = gl.GLScatterPlotItem(
                pos=np.array(self.inert_point+i+1), size=12, color=(0,1,0,1)
            )
            self.view.addItem(vive_pos)

            #init vive axes plot
            vive_axes = []
            for j, col in enumerate(self.triaxis_color):
                v = self.inert_frame[:,j]     # transform axis
                pts = np.vstack([self.inert_point+i+1,self.inert_point+i+1+v])
                plt = gl.GLLinePlotItem(pos=pts, color=col, width=3, antialias=True)
                vive_axes.append(plt)
                self.view.addItem(plt)
            self.marker_list.append({"pos":vive_pos,"rot":vive_axes})
    def update_vive(self):
        pos,frame = self.vive.get_trackers_pose()

        for i,marker in enumerate(self.marker_list):
            cur_marker_pos = np.matmul(self.inert_vive_rotation,pos[i]) # position in inertial frame
            marker["pos"].setData(pos=cur_marker_pos)

            rotation = R.from_quat(frame[i])
            cur_marker_frame =  np.matmul(self.inert_vive_rotation,rotation.as_matrix()) # orientation in inertial frame      
            for j, col in enumerate(self.triaxis_color):
                pts = np.vstack([cur_marker_pos,cur_marker_pos+cur_marker_frame[:,j]])
                marker["rot"][j].setData(pos=pts)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = FMC_Glove_eval(freq=300,num_vive_markers=2)
    w.setWindowTitle("ForceMoCap")
    w.show()
    sys.exit(app.exec_())
