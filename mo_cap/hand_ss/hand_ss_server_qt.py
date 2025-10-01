import socket
import os, sys
import time
import json

import pandas as pd
import numpy as np
np.set_printoptions(
    precision=4,
    linewidth=np.inf,   
    formatter={'float_kind': lambda x: f"{x:.4f}"}
)
from scipy.spatial.transform import Rotation as R
from spatialmath import SE3

from PySide6.QtCore import QObject, QThread, Signal,Slot,QTimer,QElapsedTimer,Qt, QMetaObject
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget

class SSHandClient(QObject):
    hand_ready = Signal(dict)
    stopped = Signal()
    def __init__(self, ip="127.0.0.1", port=9004,performer_Id="JQ",side="left",finger_len=1):
        super().__init__()
        self.side=side
        self.ip = ip
        self.port = port

        # Create a socket object
        self.buffer_message = ""
        self.json_data = None
        self.print_text = None

        # create hand data variable
        self.finger_df = None
        self.global_cache = {}
        self.finger_arr_index = {key: idx for idx, key in enumerate(["name","parent","local_T","global_t","global_R"])}

        cur_performer_path = os.path.join(f"{os.path.dirname(__file__)}/hand_measurements/{performer_Id}", f"{side}.csv")
        try:
            bone_df = pd.read_csv(cur_performer_path)
        except Exception as e:
            print(f"{e}: No {performer_Id}'s hand")
            assert 0 
        self.bone_lengths = bone_df[["length(cm)"]].values

        # init wrist pose
        T = np.eye(4,4)
        if self.side == "left":
            self.vive_to_hand_rot = SE3.Ry(90, 'deg') * SE3.Rz(180, 'deg')
            T[:3, 3] = np.array([1,0,0])
            self.multiplier = 1
        elif self.side == "right":
            self.vive_to_hand_rot = SE3.Ry(90, 'deg')
            T[:3, 3] = np.array([-1,0,0])
            self.multiplier = -1
        self.wrist_pose = SE3(T)

        # init force response
        self.force_response = np.array([1,1,1,1,1,1,1,1,1])*10
        # self.force_response = np.zeros(9)

        # FPS Calculator
        self.hand_timer = QElapsedTimer() # use the system clock
        self.hand_timer.start()
        self.hand_frame_count = 0
        self.hand_fps = 0
        self.hand_cur_time = self.hand_timer.elapsed()
        self.hand_last_time = self.hand_timer.elapsed()

    """
    TCP Connection Functions
    """
    def reconnect(self):
        while True:
            try:
                # Create a socket object
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # set client buffer
                self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 5000)
                self.client_socket.connect((self.ip, self.port))
                break
            except Exception as e:
                print(e)
                time.sleep(1)

    """
    Hand Engine Helper Function and Callback
    """
    def change_name(self,s):
        name_token = s.split('_')
        new_name= name_token[0]+"_end_"+name_token[2]
        return new_name
    def add_distals(self,fingers_dict,distal_ids):
        # adjust dictionary by reference
        # adjust names
        distal_names = []
        for distal_id in distal_ids:
            distal_name = self.change_name(fingers_dict["names"][distal_id])
            distal_names.append(distal_name)
        fingers_dict["names"] = fingers_dict["names"]+distal_names
        # adjust parents 
        fingers_dict["parents"] = fingers_dict["parents"]+distal_ids
        # add quat and translation arr
        distal_quat_arr = np.tile(np.array([0, 0, 0, 1]), (len(distal_ids), 1))
        fingers_dict["quat_arr"] = np.vstack((fingers_dict["quat_arr"],distal_quat_arr))
        distal_trans_arr = np.tile(np.array([self.multiplier*1,0,0]), (len(distal_ids), 1))
        fingers_dict["trans_arr"] = np.vstack((fingers_dict["trans_arr"],distal_trans_arr))
    def add_palm_spots(self,fingers_dict):

        # add thumb 
        palm0 = "palm_0"
        fingers_dict["names"].append(palm0)
        fingers_dict["parents"].append(5)
        palm0_trans = (fingers_dict["global_t_arr"][5]+fingers_dict["global_t_arr"][6])/2
        palm0_quat = fingers_dict["global_quat_arr"][5]

        fingers_dict["global_t_arr"] = np.vstack((fingers_dict["global_t_arr"],palm0_trans))
        fingers_dict["global_quat_arr"] = np.vstack((fingers_dict["global_quat_arr"],palm0_quat))

        # add index-mid 
        palm1 = "palm_1"
        fingers_dict["names"].append(palm1)
        fingers_dict["parents"].append(-1)
        palm1_trans = (fingers_dict["global_t_arr"][2]+fingers_dict["global_t_arr"][17])/2
        palm1_quat = fingers_dict["global_quat_arr"][2]

        fingers_dict["global_t_arr"] = np.vstack((fingers_dict["global_t_arr"],palm1_trans))
        fingers_dict["global_quat_arr"] = np.vstack((fingers_dict["global_quat_arr"],palm1_quat))

        # add mid-ring 
        palm2 = "palm_2"
        fingers_dict["names"].append(palm2)
        fingers_dict["parents"].append(-1)
        palm2_trans = (fingers_dict["global_t_arr"][17]+fingers_dict["global_t_arr"][9])/2
        palm2_quat = fingers_dict["global_quat_arr"][17]

        fingers_dict["global_t_arr"] = np.vstack((fingers_dict["global_t_arr"],palm2_trans))
        fingers_dict["global_quat_arr"] = np.vstack((fingers_dict["global_quat_arr"],palm2_quat))

        # add ring-pinky 
        palm3 = "palm_3"
        fingers_dict["names"].append(palm3)
        fingers_dict["parents"].append(-1)
        palm3_trans = (fingers_dict["global_t_arr"][9]+fingers_dict["global_t_arr"][13])/2
        palm3_quat = fingers_dict["global_quat_arr"][9]

        fingers_dict["global_t_arr"] = np.vstack((fingers_dict["global_t_arr"],palm3_trans))
        fingers_dict["global_quat_arr"] = np.vstack((fingers_dict["global_quat_arr"],palm3_quat))

    def get_global_transform_arr(self,fingers_dict):
        quats = fingers_dict["quat_arr"]# shape (N,4)
        quats[0] = np.array([0,0,0,1])# correct the rotation of wrist 
        trans = fingers_dict["trans_arr"]# shape (N,4)
        trans[0] = np.array([0,0,0])# correct the position of wrist 

        # scale to user hands (scale to cm)
        norms = np.linalg.norm(trans, axis=1,keepdims=True)
        norms[norms == 0] = 1
        actual_trans = trans / norms * self.bone_lengths

        # get gloval transformation
        N = quats.shape[0]
        rot_mats = R.from_quat(quats).as_matrix()
        # now assemble 4×4 transforms: shape (N,4,4)
        T = np.zeros((N,4,4), dtype=float)
        T[:,:3,:3] = rot_mats
        T[:,:3, 3] = actual_trans/100
        T[:, 3, 3] = 1

        global_T_list = []
        global_t_list = []
        global_R_list = []
        for i,(parent,local_T) in enumerate(zip(fingers_dict["parents"],T)):
            if (parent == -1):
                global_T_list.append(self.wrist_pose * self.vive_to_hand_rot) # the position of the wrist 
            else:
                global_T_list.append(global_T_list[parent] * SE3(local_T)) # {0}_{p}R * {p}_{c}R
            global_t_list.append(global_T_list[i].t)
            global_R_list.append(global_T_list[i].R)
        fingers_dict["global_T_list"] = global_T_list
        fingers_dict["global_t_arr"] = np.array(global_t_list)
        fingers_dict["global_quat_arr"] =  R.from_matrix(np.array(global_R_list)).as_quat()  # order (x, y, z, w)
    def circular_TCP(self):
        # extract packet with a circular buffer
        MARKER = b'\x00\x00\x11'
        self.buffer_message += self.client_socket.recv(4000).decode('utf-8',errors='replace')
        json_start = self.buffer_message.find(MARKER.decode('utf-8',errors='replace'))
        json_end = self.buffer_message.find(']}')
        while json_end == -1:
            self.buffer_message += self.client_socket.recv(500).decode('utf-8',errors='replace') # add another buffer of message in case not enuf
            json_start = self.buffer_message.find(MARKER.decode('utf-8',errors='replace'))
            json_end = self.buffer_message.find(']}')

        json_string = self.buffer_message[json_start+4:json_end+2]
        # restart the message with the leftovers
        self.buffer_message = self.buffer_message[json_end+2:] 
        return json_string
    def read_fingers_data(self):
        # read Glove Data
        try:
            # update FPS
            self.hand_frame_count += 1
            self.hand_cur_time = self.hand_timer.elapsed()
            if self.hand_cur_time-self.hand_last_time >= 1000:
                self.hand_fps = self.hand_frame_count * 1000 / (self.hand_cur_time-self.hand_last_time)
                self.hand_last_time = self.hand_cur_time
                self.hand_frame_count = 0
            
            # process finger data
            json_string =self.circular_TCP()
            self.json_data = json.loads(json_string)  # Convert to dictionary
            self.time = self.json_data['timecode']
            self.print_text = f"{self.time}\n"
        except Exception as e:
            print("Over extension detected",e)
            data = {
                "fingers_dict":self.fingers_dict,
                "print_text":"Error",
                "hand_fps":self.hand_fps
            }
            self.hand_ready.emit(data)
        else:
            # clean up the raw_df for efficieny
            raw_df = pd.DataFrame(self.json_data['bones']) 
            names = raw_df["name"].tolist()
            parents = raw_df["parent"].tolist()
            quat_arr = np.array(raw_df["rotation"].tolist())
            trans_arr = np.array(raw_df["translation"].tolist())
            self.fingers_dict = {
                "names":names,
                "parents":parents,
                "quat_arr":quat_arr,
                "trans_arr":trans_arr
            }
            

            self.add_distals(self.fingers_dict,distal_ids = [7,4,19,11,15])
            self.get_global_transform_arr(self.fingers_dict)
            self.add_palm_spots(self.fingers_dict)
            

            # process print text and force vectors
            force_vecs = np.zeros((9,3))
            for i,distal in enumerate([20,21,22,23,24,25,26,27,28]):
                pos = self.fingers_dict["global_t_arr"][distal]
                rot = R.from_quat(self.fingers_dict["global_quat_arr"][distal]).as_matrix()

                name = self.fingers_dict["names"][distal]
                force_pos_vector = rot[:,1]*self.multiplier*self.force_response[i] # multiply the normal vector with the force magnitude
                force_vecs[i,:] = force_pos_vector
                self.print_text += f"{name:<12}: {pos}\tforce vector: {force_pos_vector}\n"
                # print(f"{name:<20}:")
            self.print_text += f"Net Force: \t\t\t\tforce vector: {np.sum(force_vecs,axis=0)}"

            self.fingers_dict["force_vecs"] = force_vecs
            # emit the signal
            data = {
                "fingers_dict":self.fingers_dict,
                "print_text":self.print_text,
                "hand_fps":self.hand_fps
            }
            self.hand_ready.emit(data)

    """
    Initialization Callback
    """
    def start_worker(self):
        self.reconnect()
        self.poll_timer = QTimer()
        self.poll_timer.setTimerType(Qt.PreciseTimer)
        self.poll_timer.timeout.connect(self.read_fingers_data)
        self.poll_timer.start(int(1/200*1000)) # run timer at higher frequency than the glove since we cannot refresh TCP to get latest message
    
    """
    External Signals Callbacks
    """
    @Slot(list)
    def update_wrist(self,vive_response):
        if self.side == "left":
            cur_marker_pos = vive_response["wrists_pos"]["LHR-C700522C"] # position of wrist in inertial frame
            cur_marker_frame = R.from_quat(vive_response["wrists_frame"]["LHR-C700522C"]).as_matrix()
            T = np.eye(4,4)
            T[:3,:3] = cur_marker_frame
            T[:3, 3] = cur_marker_pos
            self.wrist_pose = SE3(T)
        elif self.side == "right":
            cur_marker_pos = vive_response["wrists_pos"]["LHR-26922E89"] # position of wrist in inertial frame
            cur_marker_frame = R.from_quat(vive_response["wrists_frame"]["LHR-26922E89"]).as_matrix()
            T = np.eye(4,4)
            T[:3,:3] = cur_marker_frame
            T[:3, 3] = cur_marker_pos
            self.wrist_pose = SE3(T)
    @Slot(list)
    def update_force(self,force_response):
        self.force_response = force_response["force_data"]
    @Slot()
    def stop(self):
        # print("HELO")
        try:
            self.client_socket.shutdown(socket.SHUT_WR)
        except OSError:
            pass
        finally:
            self.client_socket.close()
        self.poll_timer.stop()
        self.stopped.emit()

# ----------------------------
# Main application window
# ----------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QThread Example")

        # import debugpy
        # debugpy.listen(("localhost", 5678))
        # print("Waiting for debugger…")
        # debugpy.wait_for_client()

        # Label to display data
        self.label = QLabel("Waiting for data...")
        self.button = QPushButton("Stop Thread")

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Setup thread and worker
        self.thread = QThread()
        self.worker = SSHandClient(port=9004,performer_Id="JQ",side="left")
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.start_worker)
        self.worker.hand_ready.connect(self.update_label)
        self.button.clicked.connect(self.cleanup)

        self.thread.start()

    def update_label(self, text):
        self.label.setText(f'{text["print_text"]}')

    def cleanup(self):
        QMetaObject.invokeMethod(self.worker, "stop", Qt.ConnectionType.QueuedConnection)
        self.worker.stopped.connect(self.thread.exit)
        self.label.setText("Thread stopped.")

        import time
        time.sleep(0.3) 
        self.close()
# ----------------------------
# Application entry point
# ----------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())