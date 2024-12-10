"""
Barebone Experiment Template Code to stream xsens and openvr
- change the for loops for the experiment sessions according to your requirements
- fully controlled using space bar
- xsens done in TCP
- openvr - ?
- cannot control sampling frequency
"""
import sys
import time
import os
from blessed import Terminal
import socket

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from util_files.jq_util import *
import ForceMoCap.mo_cap.vr.openvr_util as openvr_util
from ForceMoCap.mo_cap.xsens.xsens_util import parse_header,parse_UL_joint_angle,start_xsens_TCP,start_xsens_UDP

"set arguments"
if len(sys.argv) >= 2:
    interval = 1/70
    num_tracker = int(sys.argv[1])
    info_num = int(sys.argv[2])
    subject_id = int(sys.argv[3])
    hand_side = int(sys.argv[4])
    num_of_tasks = int(sys.argv[5])
    num_of_configs = int(sys.argv[6])
    num_of_reps = int(sys.argv[7])
else:
    interval = 1/60
    info_num = 2
    num_tracker = 3
    subject_id = 0 
    hand_side = 'r'
    num_of_tasks = 4
    num_of_configs = 6
    num_of_reps = 3
    exp_id = "exp_1_data"

"for trial repetition purposes if experiment stop halfway"
cur_task = 1
cur_config = 1
cur_rep = 1
subject_details = {"subject_id":subject_id,
                   "num_of_task":num_of_tasks,
                   "num_of_configs":num_of_configs,
                   "num_of_reps":num_of_reps}

"create subject folder if not created"
subject_folder_path = f"./{exp_id}/sessions/sub{subject_id}"
check_subject_exist(subject_folder_path,num_of_tasks)

"start the console terminal for Dynamic Console Logging"
term = Terminal()
with term.fullscreen():
    """
    Print Experiment Details
    """
    print(term.home + term.bold(f"===========Experiment Details======================="))
    terminal_pos = 1
    for i,key in enumerate(subject_details.keys()):
        print(term.bold(f"{key}:{subject_details[key]}"))

    """
    start the VR platform and print VR details
    """
    v = openvr_util.triad_openvr()
    tracker_details = ["=========VIVE Details=========="] + v.get_discovered_objects() +["=================="] 
    for i, message in enumerate(tracker_details):
        print(term.bold(message))
    terminal_pos += len(tracker_details) + len(subject_details)


    for task in range(cur_task-1,num_of_tasks): # edit these 3 for loops based on experiment requirem ents
        for config in range(cur_config-1,num_of_configs):
            for rep in range(cur_rep-1,num_of_reps):

                """
                Actual Data Logging starts here
                """
                trial_good = False
                while trial_good is not True:
                    print(term.move(terminal_pos, 0) + term.clear_eos() + term.bold(f"Press Space to Start /  End - task:{task+1} config:{config+1} rep:{rep+1}")+term.clear_eos())
                    start = False
                    while start == False:
                        with term.cbreak():
                            key = term.inkey()
                            if key == ' ':
                                start = True

                    """
                    Start the TCP XSENS platform with a clear buffer
                    """
                    sock,conn,addr = start_xsens_TCP(timeout=interval+0.1) # wait for the xsens TCP client to connect

                    """
                    Initialize trial
                    """
                    trial_finished = False
                    trial_start = time.time()
                    data_trial = []

                    """
                    Start Trial
                    """
                    while trial_finished is not True:
                        console_log = f"=======================================\nConnection: {addr}, task:{task+1} config:{config+1} rep:{rep+1} Ongoing\n"
                        data_sample = []
                        time_elapsed = time.time()-trial_start
                        console_log += f"Time: {time_elapsed}\n"
                        data_sample.append(time_elapsed)

                        sample_start = time.time() # to log sampling frequency

                        """
                        XSENS Acquisition
                        """
                        console_log += "=========XSENS==========\n"
                        try:
                            message = conn.recv(584) 
                            header = parse_header(message[0:24]) # parse key info into header first
                            if header['message_id'] == 'MXTP20':
                                right,left = parse_UL_joint_angle(message=message[24:])
                                for key in right.keys():
                                    console_log += f"{key:15}: {left[key]:8.4f} {right[key]:8.4f}\n"
                                    if hand_side == 'r':
                                        data_sample.append(right[key])
                                    else:
                                        data_sample.append(left[key])
                        except socket.timeout: # when xsens stop sampling during playback, stop the trial
                            for key in right.keys():
                                console_log += f"{key:15}: {left[key]:8.4f} {right[key]:8.4f}\n"
                                if hand_side == 'r':
                                    data_sample.append(right[key])
                                else:
                                    data_sample.append(left[key])
                            trial_finished = True

                        """
                        Vive Acquisition
                        """
                        # notify if a tracker is lost, if not, print euler detail in every tracker
                        console_log += "=========VIVE==========\n"
                        lost = False
                        for i in range(num_tracker):
                            console_log += f"Tracker {i+1}:"
                            position,euler,quat,t_mat,valid =  v.devices[f"tracker_{i+1}"].get_all_pose() # return the pose in euler (ZYX) and transformation matrix
                            
                            for each in position+quat:
                                console_log += "%8.4f" % each
                                console_log += " "
                                data_sample.append(each)
                            if not valid:
                                console_log += "Lost \n" # lost data are all 0
                            else:
                                console_log += "\n"

                        """
                        Log Sampling Frequency
                        """
                        sampling_freq = 1/(time.time()-sample_start+0.00001)
                        data_sample.insert(1,sampling_freq)
                        string = "sampling freq"
                        console_log += f"{string:15}: {sampling_freq:.4f} Hz"

                        print(term.move(terminal_pos+1, 0) + term.clear_eos() + console_log)
                        data_trial.append(data_sample)

                        "wait for stop signal"
                        with term.cbreak():
                            key = term.inkey(0) # reminder to change the 0.01 default time delay to maximize sampling rate
                            if key == ' ':
                                trial_finished = True  
                    print()
                    print(f"task:{task+1} config:{config+1} rep:{rep+1} Finished")
                    print(term.bold(f"Is task:{task+1} config:{config+1} rep:{rep+1} Good? Press y"))

                    "repeat trial if trial is shit"
                    with term.cbreak():
                        key = term.inkey()
                        if key == 'y':
                            trial_good = True
                            columns  =["t","freq"] + [key for key in right.keys()] + [f"{letter}{i}" for i in range(1, num_tracker+1) for letter in ["x", "y", "z", "qx","qy","qz","w"]]
                            df = pd.DataFrame(data_trial, columns=columns)
                            df.to_csv(f"{subject_folder_path}/task{task+1}/m{config}d{rep}_{hand_side}.csv", index=False)  
                            p = 0
                        else:
                            trial_good = False

                    # close the client and server sockets to clear the buffer 
                    conn.close()
                    sock.close()
                    """
                    Data Logging Ends Here
                    """

        # reset for experiment repetition - not for trial repetition
            cur_rep = 1
        cur_config = 1