import serial
import time
import sys,os
sys.path.append(os.path.join(os.path.dirname(__file__)))

import time
from rft_uart_server import *

PORT = "COM7"

if __name__ == "__main__":
    rft = RFTSeriesServer(PORT)
    rft.sendCommand(COMMAND_STOP_FT_DATA_OUTPUT)
    time.sleep(0.1)
    rft.ser.flush()
    rft.sendCommand(COMMAND_READ_MODEL_NAME)
    time.sleep(0.1)
    print(responseReadModelName(rft.getResponse(ID_READ_MODEL_NAME)))
    rft.sendCommand(COMMAND_READ_SERIAL_NUMBER)
    time.sleep(0.1)
    print(responseReadSerialNUmber(rft.getResponse(ID_READ_SERIAL_NUMBER)))
    rft.sendCommand(COMMAND_READ_DATA_OUTPUT_RATE)
    time.sleep(0.1)
    print(responseReadDataOutputRate(rft.getResponse(ID_READ_DATA_OUTPUT_RATE)))
    rft.sendCommand(COMMAND_START_FT_DATA_OUTPUT)
    time.sleep(0.1)
    rft.sendCommand(commandSetFilter(1,10))
    time.sleep(0.1)
    # rft.softTare()
    rft.hardTare()
    # while True:
    #     # print(responseReadFTData(rft.getResponse(ID_START_FT_DATA_OUTPUT)))
    #     print(f"{rft.getTareFT()[0]:>9.4f}, {rft.getTareFT()[1]:>9.4f}, {rft.getTareFT()[2]:>9.4f}, {rft.getTareFT()[3]:>9.4f}, {rft.getTareFT()[4]:>9.4f}, {rft.getTareFT()[5]:>9.4f}")
    #     time.sleep(1/50)
    #     rft.ser.flush()
    # rft.sendCommand(COMMAND_STOP_FT_DATA_OUTPUT)
