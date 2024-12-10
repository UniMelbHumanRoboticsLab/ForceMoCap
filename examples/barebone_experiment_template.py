"""
Barebone Experiment Template Code
- change the for loops for the experiment sessions according to your requirements
"""
import sys
import time
import os
import socket
from blessed import Terminal

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import ForceMoCap.mo_cap.vr.openvr_util as openvr_util
from ForceMoCap.mo_cap.xsens.xsens_util import parse_header,parse_UL_joint_angle,parse_time

"log experiment details"
subject_id = 1#input("Input Subject ID:")
num_of_tasks = 2#input("Input Number of Tasks:")
num_of_configs = 3#input("Input Number of Configs per Task:")
num_of_reps = 2#input("Input Number of Repetitions per Config:")
cur_task = 0
cur_config = 0
cur_rep = 0
subject_details = {"subject_id":subject_id,
                   "num_of_task":num_of_tasks,
                   "num_of_configs":num_of_configs,
                   "num_of_reps":num_of_reps}

"Start UDP Port for XSENS"
UDP_IP = "127.0.0.3"
UDP_PORT = 9764

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))

"start the VR platform"
v = openvr_util.triad_openvr()
tracker_details = ["=========VIVE Details=========="] + v.get_discovered_objects() +["=================="] 

"set sampling time"
if len(sys.argv) >= 2:
    interval = 1/70
    num_tracker = int(sys.argv[1])
    info_num = int(sys.argv[2])
else:
    interval = 1/500
    info_num = 2
    num_tracker = 2

"start the console terminal for dynamic console logging"
term = Terminal()

with term.fullscreen():
    """
    Print Experiment Details
    """
    print(term.home + term.bold(f"===========Experiment Details======================="))
    terminal_pos = 1
    for i,key in enumerate(subject_details.keys()):
        print(term.bold(f"{key}:{subject_details[key]}"))
    for i, message in enumerate(tracker_details):
        print(term.bold(message))
    terminal_pos += len(tracker_details) + len(subject_details)
    
    for task in range(cur_task,num_of_tasks): # edit these 3 for loops based on experiment requirements
        for config in range(cur_config,num_of_configs):
            for rep in range(cur_rep,num_of_reps):

                trial_good = False
                while trial_good is not True:
                    print(term.move(terminal_pos, 0) + term.clear_eos() + term.bold(f"Press Enter to Re-Start / Press q to End - task:{task+1} config:{config+1} rep:{rep+1}")+term.clear_eos())
                    with term.cbreak():
                        key = term.inkey()  # Waits for a single key press

                    """
                    Start Data Logging
                    """
                    trial_finished = False
                    while trial_finished is not True:
                        start = time.time()
                        console_log = f"task:{task+1} config:{config+1} rep:{rep+1} Ongoing\n"
                        
                        """
                        TODO: Collect Data here
                        """

                        "control and log sampling frequency"
                        sleep_time = interval-(time.time()-start)
                        if sleep_time>0:
                            "get trial end signal during the sampling pause"
                            with term.cbreak():
                                # for new workstation, rmb go win_terminal.py and edit the 0.01 time when timeout is none to increase sampling rate
                                key = term.inkey(timeout=sleep_time)  
                                if key: # if key is pressed
                                    if key == 'q':  # Exit the loop on 'q'
                                        break
                        sampling_freq = 1/(time.time()-start)
                        string = "sampling freq"
                        console_log += f"{string:15}: {sampling_freq:.4f} Hz"

                        print(term.move(terminal_pos+1, 0) + term.clear_eos() + console_log)


                    print()
                    print(f"task:{task+1} config:{config+1} rep:{rep+1} Finished")
                    print(term.bold(f"Is task:{task+1} config:{config+1} rep:{rep+1} Good? Press y"))
                    with term.cbreak():
                        key = term.inkey()
                        if key == 'y':
                            trial_good = True
                        else:
                            trial_good = False