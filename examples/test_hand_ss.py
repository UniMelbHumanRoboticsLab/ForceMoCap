"""Small example OSC server

This program listens to several addresses, and prints some information about
received packets.
"""
import argparse
import time
import sys,os
import numpy as np
np.set_printoptions(suppress=True,precision=4) # suppress scientific notation
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from mo_cap.hand_ss.hand_ss_util import SSHandServer

if __name__ == "__main__":
    server = SSHandServer()
    start = time.time()
    i = 0

    while True:
        i +=1
        quat,pos = server.get_finger_data()
        # print(f"Distal Quat: {quat}")
        print(f"Distal Pos: {pos}")
        print()

    print(f"{i} samples")
  