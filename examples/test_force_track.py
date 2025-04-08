# a python program to send an initial packet, then listen for packets from the ESP32
# the laptop/rasp pi that this code runs on can still be connected to the internet, but should also "share" its connection by creating its own mobile hotspot
# this version of the code allows your laptop to remain connected to the internet (which is a postive)
# but requires configuring your laptop to share its internet connection (which can be a negative because it is tricky to set up depending on your OS)
# for version that does not require sharing an internet connection, see https://gist.github.com/santolucito/70ecb94ce297eb1b8b8034f78683447b 

import socket
SERVER_IP = "192.168.0.94"
FINGER1_IP = "192.168.0.96" # The IP that is printed in the serial monitor from the ESP32_1
PALM1_IP = "192.168.0.95" # The IP that is printed in the serial monitor from the ESP32_2
FINGER1_PORT = 4210
PALM1_PORT = 4211
timeout = 10
finger1_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Internet  # UDP
finger1_sock.bind((SERVER_IP,FINGER1_PORT)) 
finger1_sock.connect((FINGER1_IP, FINGER1_PORT))
finger1_sock.settimeout(timeout)

palm1_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Internet  # UDP
palm1_sock.bind((SERVER_IP,PALM1_PORT)) 
palm1_sock.connect((PALM1_IP, PALM1_PORT))
palm1_sock.settimeout(timeout)

def loop():
    while True:
        # data = finger1_sock.recv(2048)
        # print(f"1:{data}")
        data = palm1_sock.recv(8096)
        # decode to 12 values
        print(data)

if __name__ == "__main__":
    # finger1_sock.send('Start ESP1'.encode()) # message to bypass NAT restriction
    palm1_sock.send('Start PALM1'.encode())
    loop()