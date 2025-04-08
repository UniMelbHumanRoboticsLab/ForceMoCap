import numpy as np
import struct
import socket
np.set_printoptions(suppress=True, precision=10)

"Function to Start UDP Port for force_esp32"
def start_force_esp32_UDP():
    UDP_IP = "192.168.0.94"
    UDP_PORT = 2335
    sock = socket.socket(socket.AF_INET, # Internet
                        socket.SOCK_DGRAM) # UDP
    sock.bind((UDP_IP, UDP_PORT))
    return sock

