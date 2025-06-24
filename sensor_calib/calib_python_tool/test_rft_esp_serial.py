# script to test restarting the serial from ESP and RFT

import sys
import os
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from force_tracking.firmware.python.pyRFT.rft_uart_server import *
from force_tracking.firmware.python.esp_serial.esp_serial_server import *

np.set_printoptions(
    precision=4,
    linewidth=np.inf,   
    formatter={'float_kind': lambda x: f"{x:.4f}"}
)

PORT_ESP = "COM8"
esp = ESPSeriesServer(PORT_ESP)

PORT_RFT = "COM7"
rft = RFTSeriesServer(port = "COM7")
rft.init_and_collect()

i = 0
while True:
    print(i,esp.get_mlx_data(),rft.getTareFT())
    i += 1
    # if i == 10000:
    #     i = 0
    #     esp.restart()
    #     esp.wait_calibrate()

    #     rft.restart()
    #     rft.init_and_collect()

