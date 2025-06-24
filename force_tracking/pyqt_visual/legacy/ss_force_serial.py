import os, sys
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph.opengl as gl
from spatialmath import SE3,SO3

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from firmware.python.esp_serial.esp_serial_server import ESPSeriesServer

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from mo_cap.hand_ss.hand_ss_server import SSHandClient

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
        

class SS_Force_Serial(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.resize(600, 600)
        
        self.layout = QtWidgets.QVBoxLayout(self)
        self.fps_label = QtWidgets.QLabel("FPS: 0.00")
        self.fps_label.setFixedSize(600,20)
        self.layout.addWidget(self.fps_label)

        # 3D view
        self.view = FullRotateGLViewWidget(rotationMethod='quaternion')
        self.view.opts['distance'] = 6
        self.view.opts['fov'] = 30
        # ground grid
        grid = gl.GLGridItem(size = QtGui.QVector3D(1,1,1))
        grid.setSpacing(0.1, 0.1, 0.1)
        self.view.addItem(grid)
        self.layout.addWidget(self.view)
        # inertial frame
        inert_frame = SO3().R
        for j, col in enumerate([(1,0,0,1),(0,1,0,1),(0,0,1,1)]):
            v = inert_frame[:,j]     # transform axis
            pts = np.vstack([np.array([[0,0,0]]), np.array([[0,0,0]])+v])
            plt = gl.GLLinePlotItem(pos=pts, color=col, width=3, antialias=True)
            self.view.addItem(plt)
        self.setLayout(self.layout)

        # initialize glove               
        self.hands = {}
        self.bone_num = 16
        ports = [9004,9003]
        for idx,side in enumerate(["left"]):
            hand = {}

            #init skeleton plot
            skeleton = {}
            # init bones
            skeleton["bones"] = []
            for i in range(self.bone_num):
                # dont plot bone for wrist
                if i != 0:
                    bone = gl.GLLinePlotItem(pos=np.vstack([np.array([[0,0,0]]), np.array([[0.5,0.5,0.5]])]), color=(0,0,1,1), width=3, antialias=True)
                    skeleton["bones"].append(bone)
                    self.view.addItem(bone)

            # init distals
            skeleton["distals"] = {}   
            bv = SO3().R * 0.1             
            for i in ["hand","thumb_03","index_03","middle_03","ring_03"]:
                #init distal pos plot
                distal = gl.GLScatterPlotItem(
                    pos=np.array([[0,0,0]]), size=12, color=(0,1,0,1)
                )
                self.view.addItem(distal)

                #init distal frame plot
                axes = []
                for j, col in enumerate([(1,0,0,1),(0,1,0,1),(0,0,1,1)]):
                    v = bv[:,j]     # transform axis
                    pts = np.vstack([np.array([[0,0,0]]), np.array([[0,0,0]])+v])
                    plt = gl.GLLinePlotItem(pos=pts, color=col, width=3, antialias=True)
                    axes.append(plt)
                    self.view.addItem(plt)

                #init distal sensor plot
                sensor = gl.GLLinePlotItem(pos=np.vstack([np.array([[0,0,0]]), np.array([[0.01,0.01,0.01]])]), color=(1,1,0,1), width=3, antialias=True)
                self.view.addItem(sensor)
                
                skeleton["distals"][i] = {"pos":distal,"rot":axes,"sensor":sensor}
            hand["skeleton"]=skeleton

            #init sensor esp
            esp,terminal_pos = reconnect_esp(1,port="COM9")
            esp.ser.reset_input_buffer() 
            hand["sensor"]=esp
        
            #init hand servers#
            SS_single = SSHandClient('127.0.0.1',ports[idx],side=side)
            hand["SS"]=SS_single

            self.hands[side]=hand

        # Timer and FPS variables
        self.frame_count = 0
        self.fps = 0
        self.elapsed_timer = QtCore.QElapsedTimer()
        self.elapsed_timer.start()

        # timer to update the point
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_skeleton)
        self.timer.start(0)
        
    def update_skeleton(self):
        for side, hand in self.hands.items():
            hand["sensor"].ser.reset_input_buffer() 
            force_data = hand["sensor"].get_force()/100000
            
            fingers_data,response = hand["SS"].return_finger_data()
            # draw hand
            if response:
                if side == "left":
                    partition = "_l"
                else:
                    partition = "_r"    

                for idx in range(self.bone_num):
                    bone = fingers_data.iloc[idx]
                    pos = bone['T_global'].t # position from inertial to bone
                    # plot bones
                    if bone['parent'] != -1:
                        hand["skeleton"]["bones"][idx-1].setData(pos=np.vstack([pos, fingers_data.loc[bone['parent'],'T_global'].t]))
                    # plot distals
                    if "hand" in bone['name'] or "03" in bone['name']:
                        bone_name = bone['name'].partition(partition)[0]
                        # plot the wrist and distals pos
                        hand["skeleton"]["distals"][bone_name]['pos'].setData(pos=pos)
                        # plot wrist and distals frame
                        rot = bone['T_global'].R # rotation from inertial to distal
                        bv = SO3().R * 1/100 # 1cm distal frame
                        for i, col in enumerate([(1,0,0,1),(0,1,0,1),(0,0,1,1)]):
                            v = rot @ bv[:,i]     # transform axis
                            pts = np.vstack([pos, pos+v])
                            hand["skeleton"]["distals"][bone_name]['rot'][i].setData(pos=pts)
                        # plot distal sensors
                        # transform the force vector to be in inertial frame
                        if bone_name in finger_sensor_idx.keys():
                            rot_sen = SO3.Rz(-90, 'deg') * SO3.Rx(90, 'deg') * SO3() # rotation from sensor to distal - follow this intrinsic rotation order (rotate abt z by -90, rotate about x by 90)
                            finger_index = finger_sensor_idx[bone_name]
                            force_sf = force_data[finger_index:finger_index+3] # force in the sensor frame
                            force_df = np.matmul(np.linalg.inv(rot_sen.R),force_sf) # force in the distal frame
                            force_if = np.matmul(rot,force_df) # force in the inertial frame
                            # print(force_sf*10,force_ff*10,force_if*10)
                            hand["skeleton"]["distals"][bone_name]['sensor'].setData(pos=np.vstack([pos, pos+force_if]))
            else:
                print("Error")

        self.frame_count += 1
        # Update FPS every second
        if self.elapsed_timer.elapsed() >= 1000:
            self.fps = self.frame_count * 1000 / self.elapsed_timer.elapsed()
            self.frame_count = 0
            self.elapsed_timer.restart()
        self.fps_label.setText(f"FPS: {self.fps:.2f}, {response}")

            

            
