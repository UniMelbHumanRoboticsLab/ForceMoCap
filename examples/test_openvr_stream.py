from blessed import Terminal
import numpy as np

import sys,os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import mo_cap.vr.openvr_util as openvr_util

# start the console terminal for nice logging
term = Terminal()

# start the VR platform
v = openvr_util.triad_openvr()
tracker_details = ["=========VIVE=========="] + v.get_discovered_objects() +["=================="]

# set sampling time
if len(sys.argv) == 1:
    interval = 1/30

with term.fullscreen():
    for i, message in enumerate(tracker_details):
        print(term.move(i, 0) + term.bold(message))

        # Calculate the starting row for streaming data
        start_row = len(tracker_details)
        
    while(True):
        start = time.time()
        
        # notify if a tracker is lost, if not print euler detail in every tracker
        lost = False
        num_tracker = 2
        txt = ""
        for i in range(num_tracker):
            txt += f"Tracker {i+1}:"
            pose_euler,t_mat,valid =  v.devices[f"tracker_{i+1}"].get_pose_euler() # return the pose in euler (ZYX) and transformation matrix
            if valid:
                for each in pose_euler:
                    txt += "%8.4f" % each
                    txt += " "
                txt += "\n"
            else:
                txt += " Lost"
                txt += "\n"
                lost = True

        # print(term.move(start_row, 0) + term.clear_eol() + txt)

        sleep_time = interval-(time.time()-start)
        if sleep_time>0:
            time.sleep(sleep_time)
        
        sampling_freq = 1/(time.time()-start)
        string = "sampling freq"
        txt += f"{string:15}: {sampling_freq:.4f} Hz"
        print(term.move(start_row, 0) + term.clear_eol() + txt)