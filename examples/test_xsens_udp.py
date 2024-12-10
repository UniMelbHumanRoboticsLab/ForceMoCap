import sys
import time
import os
import socket
from blessed import Terminal

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from ForceMoCap.mo_cap.xsens.xsens_util import parse_header,parse_UL_joint_angle,parse_time,start_xsens_UDP


"start the console terminal for nice logging"
term = Terminal()

"Start UDP Port for XSENS"
sock = start_xsens_UDP()

"set sampling time"
if len(sys.argv) >= 2:
    interval = 1/30
    num_tracker = int(sys.argv[1])
else:
    interval = 1/60
    num_tracker = 2

"start the logging"
with term.fullscreen():

    # log vr details
    start_row = 0
    tracker_details = ["=========XSENS=========="] + ["WELCOME"]+["=================="]

    for i, message in enumerate(tracker_details):
        print(term.move(i, 0) + term.bold(message))
        # Calculate the starting row for streaming data
    start_row += len(tracker_details)

    while(True):
        start = time.time()

        """
        XSENS Acquisition
        """
        txt = "=========XSENS==========\n"
        # loop n times if we are expecting n different UDP packets
        info_num = 2
        for i in range(info_num):
            message, addr = sock.recvfrom(4096)
            header = parse_header(message[0:24]) # parse key info into header first
            if header['message_id'] == 'MXTP20':
                right,left = parse_UL_joint_angle(message=message[24:])
                for key in right.keys():
                    txt += f"{key:15}: {left[key]:8.4f} {right[key]:8.4f}\n"
                # print("RIGHT:",right)
                # print("LEFT:",left)
            elif header['message_id'] == 'MXTP25' and header['character_id'] == 0:
                sampled_time = parse_time(message[-12:])
                # print("\rSampled_time:",sampled_time)
                txt += f"TIME: {sampled_time}\n"
            else:
                continue

        """
        Control Sampling Frequency
        """
        sleep_time = interval-(time.time()-start)
        if sleep_time>0:
            time.sleep(sleep_time)

        """
        Console Log
        """
        sampling_freq = 1/(time.time()-start)
        string = "sampling freq"
        txt += f"{string:15}: {sampling_freq:.4f} Hz"
        print(term.move(start_row, 0) + term.clear_eol() + txt)
        
        
