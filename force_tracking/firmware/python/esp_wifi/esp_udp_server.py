import time
import threading
import numpy as np
import socket

class EspUDPServer:
    def __init__(self, ip="192.168.6.206", port=4211):
        # Create a socket object
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        self.server_socket.bind(('', 4212)) # replace the ip with ''
        self.server_socket.sendto(bytes("HI", "utf-8"), (ip, port))
        # print("DDD")

        # print the calibration messages
        for i in range(4):
            # print("FFF")
            self.buffer = self.server_socket.recvfrom(255)[0] #print the hi message
            print(self.buffer)

        self.__thread = threading.Thread(target=self.__readResponseRunner)
        self.__thread.daemon = True
        self._lock = threading.Lock()
        self.__thread.start()
        self.buffer = 0

    def disconnect(self):
        """Cleanly close the TCP connection."""
        try:
            # Disable further sends and receives
            self.server_socket.shutdown(socket.SHUT_RDWR)
            self.connected=False
        except OSError:
            # socket might already be closed or not fully connected
            assert 0 
        finally:
            # Close the socket
            self.server_socket.close()
            # Optionally, create a new socket so you can reconnect later
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(('', 4212)) # replace the ip with ''

    def wait_calibrate(self):
        print("\nCalibrate ESP")

    def __readResponseRunner(self):
        while True:
            # with self._lock:
            self.buffer = np.array(self.server_socket.recvfrom(255)[0].decode().strip().split('\t'), dtype=float)
            # self.buffer = self.server_socket.recvfrom(255)[0]
            # print(self.buffer)
    
    def get_mlx_data(self):
        with self._lock:
            return self.buffer
        
if __name__ == "__main__":
    # esp = EspUDPServer()
    # while True:
    #     p = 0

    from blessed import Terminal
    term = Terminal()

    with term.fullscreen():
        # xsens = XSENSServer()
        # vive = OpenVRServer()
        # esp = ESPSeriesServer();
        esp = EspUDPServer()
        while True:
            data = esp.get_mlx_data()
            # if response != None:
            print(term.move(1, 0) + term.clear_eos() + f"{data}")