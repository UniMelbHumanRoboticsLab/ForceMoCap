import time
from force_tracking.firmware.python.pyRFT.rft_uart_server import *

PORT = "/dev/tty.usbserial-DB00G423"

if __name__ == "__main__":
    rft = RFTSeriesServer(PORT)
    rft.sendCommand(COMMAND_STOP_FT_DATA_OUTPUT)
    time.sleep(0.1)
    rft.ser.flush()
    rft.sendCommand(COMMNAD_READ_MODEL_NAME)
    time.sleep(0.1)
    print(responseReadModelName(rft.getResponse(ID_READ_MODEL_NAME)))
    rft.sendCommand(COMMAND_READ_SERIAL_NUMBER)
    time.sleep(0.1)
    print(responseReadSerialNUmber(rft.getResponse(ID_READ_SERIAL_NUMBER)))
    rft.sendCommand(COMMAND_READ_BAUDRATE)
    time.sleep(0.1)
    print(responseReadBaudrate(rft.getResponse(ID_READ_BAUDRATE)))
    rft.sendCommand(COMMAND_START_FT_DATA_OUTPUT)
    time.sleep(0.1)
    rft.sendCommand(commandSetFilter(1,10))
    time.sleep(0.1)
    # rft.softTare()
    rft.hardTare()
    while True:
        # print(responseReadFTData(rft.getResponse(ID_START_FT_DATA_OUTPUT)))
        print(f"{rft.getTareFT()[0]:>9.4f}, {rft.getTareFT()[1]:>9.4f}, {rft.getTareFT()[2]:>9.4f}, {rft.getTareFT()[3]:>9.4f}, {rft.getTareFT()[4]:>9.4f}, {rft.getTareFT()[5]:>9.4f}")
        time.sleep(1/50)
        rft.ser.flush()
    rft.sendCommand(COMMAND_STOP_FT_DATA_OUTPUT)
