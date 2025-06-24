import socket
import threading

import sys,os
sys.path.append(os.path.join(os.path.dirname(__file__)))
from xsens_tools import *

# MVN Analyze acts as a client, sending msgs to this server
class XSENSServer:
    def __init__(self, ip="127.0.0.5", port=9764):
        self.ip = ip
        self.port = port

        # Create a server_socket
        self.server_socket = socket.socket(socket.AF_INET, # Internet
                            socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow immediate reuse of the port
        self.server_socket.bind((ip, port))
        self.server_socket.listen(1)
        self.server_conn,addr = self.server_socket.accept()
        self.server_conn.settimeout(3)
        self.right = {}
        self.left = {}
        self.time = ""

        self.connected=True
        self.response = False

        self.__thread = threading.Thread(target=self.__readResponseRunner)
        self._lock = threading.Lock()
        self.__thread.daemon = True
        self.__thread.start()

    # whole packet from MVN analyze with TimeCode and Joint Angles
    # joint angle # bytes:  24 (header) + 28 joints*20bytes (joint angles) = 584 bytes
    # time_code # bytes:  24 (header) + 4(???) + 12 (time_code) = 40 bytes
    def __readResponseRunner(self):
        while True:
            raw_message = self.server_conn.recv(624)
            time = f"{parse_string(raw_message[-12:])}\n"
            right,left = parse_UL_joint_angle(raw_message[24:584])

            self.right=right
            self.left=left
            self.time = time

    def get_joint_angles(self):
        with self._lock:
            return self.time,self.right, self.left

if __name__ == "__main__":
    xsens = XSENSServer()
    while True:
        time,right,left = xsens.get_joint_angles()
        txt = time
        for key in right.keys():
            txt += f"{key:15}: {left[key]:8.4f} {right[key]:8.4f}\n"
        print(txt)
        pass