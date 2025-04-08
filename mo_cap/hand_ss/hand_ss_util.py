from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc import osc_tcp_server
import time

# class SSHandServer:
#     def __init__(self, ip="127.0.0.1", port=9400):
#         self.ip = ip
#         self.port = port
#         self.finger_quat = {}

#         self.dispatcher = dispatcher.Dispatcher()
#         for finger in ["Thumb"]
#         self.dispatcher.map("/v1/animation/1/1/Thumb/rotation", self.thumb_handler)

#         self.server = osc_server.BlockingOSCUDPServer((self.ip, self.port), self.dispatcher)

#     def thumb_handler(self, address, *args):
#         self.thumb = list(args)

#     def get_finger_data(self):
#         self.server.handle_request()  # Handle requests in a loop
#         return self.finger_quat

import time

class SSHandServer:
    def __init__(self, ip="127.0.0.1", port=9002,performer_Id=1):
        self.ip = ip
        self.port = port
        self.dispatcher = dispatcher.Dispatcher()
        fingers = ["Index"]#, "Index", "Middle", "Ring"]  # Assuming 4 fingers per hand

        # Map the addresses and handlers for each finger rotation on both hands
        self.finger_quat = {}
        for hand in [1]:
            for finger in fingers:
                address = f"/v1/animation/{performer_Id}/{hand}/{finger}/rotation"
                self.dispatcher.map(address, self.finger_quat_handlers(hand, finger))

        self.finger_pos = {}
        for hand in [1]:
            for finger in fingers:
                address = f"/v1/animation/{performer_Id}/{hand}/{finger}/position"
                self.dispatcher.map(address, self.finger_pos_handlers(hand, finger))

        self.server = osc_tcp_server.BlockingOSCTCPServer((self.ip, self.port), self.dispatcher)

    def finger_quat_handlers(self, hand, finger):
        # Dynamically creates a handler for each finger of each hand
        def quat_handler(address, *args):
            self.finger_quat[f"{hand}_{finger}"] = list(args)#[9:]
            # print(f"Received quat for {hand} {finger}")
        return quat_handler
    
    def finger_pos_handlers(self, hand, finger):
        # Dynamically creates a handler for each finger of each hand
        def pos_handler(address, *args):
            self.finger_pos[f"{hand}_{finger}"] = list(args)
            # print(f"Received pos for {hand} {finger}")
        return pos_handler

    def get_finger_data(self):
        self.server.handle_request()  # Handle requests in a loop
        return self.finger_quat,self.finger_pos