import sys
import time
import os
import socket
from blessed import Terminal

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from mo_cap.force_esp32.force_esp32_util import start_force_esp32_UDP


"start the console terminal for nice logging"
term = Terminal()

"Start UDP Port for XSENS"
sock = start_force_esp32_UDP()

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
    tracker_details = ["=========Force_ESP32=========="] + ["WELCOME"]+["=================="]

    for i, message in enumerate(tracker_details):
        print(term.move(i, 0) + term.bold(message))
        # Calculate the starting row for streaming data
    start_row += len(tracker_details)

    while(True):
        start = time.time()

        """
        Force_ESP32 Acquisition
        """
        txt = "=========Force_ESP32==========\n"
        # loop n times if we are expecting n different UDP packets
        message, addr = sock.recvfrom(4096)
        txt += f"Msg: {message}\n"


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
        
        
