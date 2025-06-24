#%%
import matplotlib.pyplot as plt
from spatialmath import SE3, SO3, Plane3
import numpy as np
np.set_printoptions(
    precision=4,
    linewidth=np.inf,   
    formatter={'float_kind': lambda x: f"{x:.4f}"}
)

import sys,os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from mo_cap.x_sens.xsens_server import XSENSServer
from mo_cap.vive.openvr_server import OpenVRServer
from force_tracking.firmware.python.esp_serial.esp_serial_server import ESPSeriesServer
from mo_cap.hand_ss.hand_ss_server import SSHandClient

if __name__ == "__main__":
    from blessed import Terminal
    term = Terminal()

    with term.fullscreen():
        # xsens = XSENSServer()
        vive = OpenVRServer()
        esp = ESPSeriesServer(port="COM11")
        ss = SSHandClient(port=9000)
        while True:
            finger,response = ss.return_finger_data()
            fs = esp.get_mlx_data()
            vive_data = vive.get_trackers_pose()

            # if response != None:
            print(term.move(0, 0) + term.clear_eos()  + f"{response}\n"+ f"{fs}\n"+ f"{vive_data}\n")
