import socket
import pandas as pd
import numpy as np
import json
import threading
from scipy.spatial.transform import Rotation as R
from spatialmath import SE3
np.set_printoptions(
    precision=2,
    linewidth=np.inf,
    formatter={'float_kind': lambda x: f"{x:.6f}"}
)

MARKER = b'\x00\x00\x11'
# HandEngine acts as a server, sending it to this client
class SSHandClient:
    def __init__(self, ip="127.0.0.1", port=9000,performer_Id=1,side="left"):
        self.side=side
        self.ip = ip
        self.port = port

        # Create a socket object
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.ip, self.port))
        self.connected=True
        self.buffer_message = ""

        self.json_data = None
        self.print_text = None
        self.finger_df = None
        self.global_cache = {}
        self.lock = threading.Lock()
        self.extract_TCP_packet()
        print("Cleared Buffer")

        self.__thread = threading.Thread(target=self.__readResponseRunner)
        self.__thread.daemon = True
        self.__thread.start()

    def disconnect(self):
        """Cleanly close the TCP connection."""
        try:
            # Disable further sends and receives
            self.client_socket.shutdown(socket.SHUT_RDWR)
            self.connected=False
        except OSError:
            # socket might already be closed or not fully connected
            assert 0 
        finally:
            # Close the socket
            self.client_socket.close()
            # Optionally, create a new socket so you can reconnect later
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def compute_global(self,row):
        # with respect to the inertial frame bone
        idx       = row.name           # 0…N-1
        parent    = row['parent']
        local_T   = row['T_local'] # local T from parent to child
        
        if parent == -1:
            local_T[:3, 3] = np.array([0,0,0]) # correct the translation of hand 
            G = SE3(local_T) # null motion for root
        else:
            G =  self.global_cache[parent] * SE3(local_T) 
        self.global_cache[idx] = G # transformation of current bone from inertial 
        return G

    def get_global_transf(self,raw_df):
        self.finger_df = raw_df.copy()
        # convert each row to a local transformation matrix
        quats = np.vstack(self.finger_df['rotation'].values)      # shape (N,4)
        trans = np.vstack(self.finger_df['translation'].values)   # shape (N,3)
        rot_mats = R.from_quat(quats).as_matrix()
        # now assemble 4×4 transforms: shape (N,4,4)
        N = len(self.finger_df)
        T = np.zeros((N,4,4), dtype=float)
        T[:,:3,:3] = rot_mats
        T[:,:3, 3] = trans/100
        T[:, 3, 3] = 1

        # if you want individual SE3 objects in your DataFrame:
        self.finger_df['T_local'] = list(T) # now df.loc[i,'T_se3'] is an SE3
        self.finger_df['T_global'] = self.finger_df.apply(self.compute_global, axis=1)

    def __readResponseRunner(self):
        while self.connected:
            self.extract_TCP_packet()

    def extract_TCP_packet(self):
        # extract packet
        self.buffer_message += self.client_socket.recv(4000).decode('utf-8',errors='replace')
        json_start = self.buffer_message.find(MARKER.decode('utf-8',errors='replace'))
        json_end = self.buffer_message.find(']}')
        while json_end == -1:
            self.buffer_message += self.client_socket.recv(500).decode('utf-8',errors='replace') # add another buffer of message in case not enuf
            json_start = self.buffer_message.find(MARKER.decode('utf-8',errors='replace'))
            json_end = self.buffer_message.find(']}')

        json_string = self.buffer_message[json_start+4:json_end+2]
        # print(json_string)
        self.json_data = json.loads(json_string)  # Convert to dictionary

        with self.lock:
            self.print_text = f"{self.json_data['timecode']}\n"

            raw_df = pd.DataFrame(self.json_data['bones']).drop(index=range(12, 16))
            self.get_global_transf(raw_df)

            for distal in [7,4,19,11]:
                bone = self.finger_df.loc[distal,'T_global']
                name = self.finger_df.loc[distal,'name']
                self.print_text += f"{name}: \ttranslation: {bone.t*100}\n"

        # restart the message with the leftovers
        self.buffer_message = self.buffer_message[json_end+2:] 

    def return_finger_data(self):
        with self.lock:
            return self.finger_df,self.print_text

if __name__ == "__main__":
    # from blessed import Terminal
    # term = Terminal()

    # with term.fullscreen():
        # xsens = XSENSServer()
        # vive = OpenVRServer()
        # esp = ESPSeriesServer();
    ss = SSHandClient()
    while True:
        data,response = ss.return_finger_data()
        # if response != None:
        # print(term.move(1, 0) + term.clear_eos() + response)
            
            # pass

# {"name":"jq Left",
#  "actor":"jq",
#  "deviceID":2,
#  "timecode":"19:49:08:117",
#  "side":0,
#  "poseName":
#  "NA","poseID":-1,
#  "poseActive":False,w
#  "poseConf":0,
#  "frameRate":120,
#  "bones":[{"name":"hand_r","parent":-1,"rotation":[2.4925e-8,0.043619,1.5192e-9,0.99905],"pre_rotation":[0,0,0,1],"post_rotation":[0,0,0,1],"scale":[1,1,1],"translation":[-26.975,0.000015259,-0.0000038147],"rotation_order":"ZYX"},
#           {"name":"pinky_00_r","parent":0,"rotation":[-0.14927,-0.13886,0.08444,0.97535],"pre_rotation":[0,0,0,1],"post_rotation":[0,0,0,1],"scale":[1,1,1],"translation":[-4.1285,-1.2054,-2.2701],"rotation_order":"ZYX"},
#           {"name":"pinky_01_r","parent":1,"rotation":[0.14545,0.096186,-0.090871,0.98048],"pre_rotation":[0,0,0,1],"post_rotation":[0,0,0,1],"scale":[1,1,1],"translation":[-5.3703,-0.0000010917,-1.078e-7],"rotation_order":"ZYX"},
#           {"name":"pinky_02_r","parent":2,"rotation":[4.572e-19,4.4716e-16,2.8509e-9,1],"pre_rotation":[0,0,0,1],"post_rotation":[0,0,0,1],"scale":[1,1,1],"translation":[-2.8638,-0.000076286,-0.0000057211],"rotation_order":"ZYX"},
#           {"name":"pinky_03_r","parent":3,"rotation":[1.4268e-19,-8.5877e-18,8.897e-10,1],"pre_rotation":[0,0,0,1],"post_rotation":[0,0,0,1],"scale":[1,1,1],"translation":[-2.1503,0.00032045,-0.000034332],"rotation_order":"ZYX"},
#           {"name":"thumb_01_r","parent":0,"rotation":[0.52133,0.47771,-0.47771,0.52133],"pre_rotation":[0,0,0,1],"post_rotation":[0,0,0,1],"scale":[1,1,1],"translation":[-4.3426,-2.2962,2.8641],"rotation_order":"ZYX"},
#           {"name":"thumb_02_r","parent":5,"rotation":[0,0,0,1],"pre_rotation":[0,0,0,1],"post_rotation":[0,0,0,1],"scale":[1,1,1],"translation":[-3.9458,0.00011444,0.000061035],"rotation_order":"ZYX"},
#           {"name":"thumb_03_r","parent":6,"rotation":[0,0,0,1],"pre_rotation":[0,0,0,1],"post_rotation":[0,0,0,1],"scale":[1,1,1],"translation":[-3.7468,-0.014587,-0.00035095],"rotation_order":"ZYX"},
#           {"name":"ring_00_r","parent":0,"rotation":[-0.081161,-0.10168,0.039271,0.99072],"pre_rotation":[0,0,0,1],"post_rotation":[0,0,0,1],"scale":[1,1,1],"translation":[-4.3768,-0.78555,-1.1333],"rotation_order":"ZYX"},
#           {"name":"ring_01_r","parent":8,"rotation":[0.079371,0.05837,-0.042774,0.99422],"pre_rotation":[0,0,0,1],"post_rotation":[0,0,0,1],"scale":[1,1,1],"translation":[-5.8208,0.044267,0.066013],"rotation_order":"ZYX"},
#           {"name":"ring_02_r","parent":9,"rotation":[-2.7861e-16,5.5457e-16,-5.9933e-10,1],"pre_rotation":[0,0,0,1],"post_rotation":[0,0,0,1],"scale":[1,1,1],"translation":[-4.4299,0.000076304,-0.000020012],"rotation_order":"ZYX"},
#           {"name":"ring_03_r","parent":10,"rotation":[5.5642e-19,2.8343e-19,3.153e-10,1],"pre_rotation":[0,0,0,1],"post_rotation":[0,0,0,1],"scale":[1,1,1],"translation":[-3.1671,0.000076298,-0.0000018962],"rotation_order":"ZYX"},
#           {"name":"middle_00_r","parent":0,"rotation":[-0.052863,-0.03725,-0.011215,0.99784],"pre_rotation":[0,0,0,1],"post_rotation":[0,0,0,1],"scale":[1,1,1],"translation":[-4.5074,-0.54211,0.14801],"rotation_order":"ZYX"},
#           {"name":"middle_01_r","parent":12,"rotation":[0.053302,-0.006311,0.008899,0.99852],"pre_rotation":[0,0,0,1],"post_rotation":[0,0,0,1],"scale":[1,1,1],"translation":[-6.366,0.046203,-0.0083696],"rotation_order":"ZYX"},
#           {"name":"middle_02_r","parent":13,"rotation":[-2.0822e-16,1.665e-16,-1.8091e-10,1],"pre_rotation":[0,0,0,1],"post_rotation":[0,0,0,1],"scale":[1,1,1],"translation":[-4.9499,-0.00013739,0.0000076323],"rotation_order":"ZYX"},
#           {"name":"middle_03_r","parent":14,"rotation":[1.9527e-20,1.09e-20,6.6764e-11,1],"pre_rotation":[0,0,0,1],"post_rotation":[0,0,0,1],"scale":[1,1,1],"translation":[-3.2283,0.000030477,1.8886e-9],"rotation_order":"ZYX"},
#           {"name":"index_00_r","parent":0,"rotation":[0.0073405,0.025826,-0.0039433,0.99963],"pre_rotation":[0,0,0,1],"post_rotation":[0,0,0,1],"scale":[1,1,1],"translation":[-4.3351,-0.69115,1.5983],"rotation_order":"ZYX"},
#           {"name":"index_01_r","parent":16,"rotation":[-0.0071615,-0.069405,0.0042597,0.99755],"pre_rotation":[0,0,0,1],"post_rotation":[0,0,0,1],"scale":[1,1,1],"translation":[-6.5023,0.0075861,-0.004068],"rotation_order":"ZYX"},
#           {"name":"index_02_r","parent":17,"rotation":[-2.2206e-16,3.3309e-16,-3.2231e-11,1],"pre_rotation":[0,0,0,1],"post_rotation":[0,0,0,1],"scale":[1,1,1],"translation":[-4.9162,0.000091638,-0.00007486],"rotation_order":"ZYX"},
#           {"name":"index_03_r","parent":18,"rotation":[3.2548e-22,-6.6907e-22,8.491e-13,1],"pre_rotation":[0,0,0,1],"post_rotation":[0,0,0,1],"scale":[1,1,1],"translation":[-2.6394,0.00012212,-0.000011919],"rotation_order":"ZYX"}]
# }