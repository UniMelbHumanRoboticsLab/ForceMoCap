import serial
import time
import threading
import numpy as np
import sys,os
sys.path.append(os.path.join(os.path.dirname(__file__)))
from RFT_UART_command import *
from RFT_UART_response import *

class RFTSeriesServer:
    __response = dict()
    DT = 50
    DF = 1000
    offsetFx, offsetFy, offsetFz, offsetTx, offsetTy, offsetTz = 0, 0, 0, 0, 0, 0
    def __init__(self, port, baud=115200):
        # default 115200 bps
        # 1 stop bit, No parity, No flow control, 8 data bits
        self.port = port
        self.baud = baud
        self.ser = serial.Serial(port, baud)
        self.restart()
        self.__thread = threading.Thread(target=self.__readResponseRunner)
        self.__thread.daemon = True
        self.__thread.start()
    def close(self):
        self.ser.flush()
        self.ser.close()
        self.on = False
    def restart(self):
        self.close()
        self.ser = serial.Serial(self.port, self.baud)
        self.on = True
    def init_and_collect(self):
        print("\nInitialize RFT")
        self.init_rft()
        self.sendCommand(COMMAND_START_FT_DATA_OUTPUT)
        
    ## Command Packet Structure
    # SOP : 0x55
    # Data Field  : 8 bytes
    # Checksum : 1 byte, summation of data field
    # EOP : 0xAA
    def sendCommand(self, command):
        if len(command) != 8:
            raise ValueError('Data field must be 8 bytes long')
        packet = b'\x55' + command + int.to_bytes(sum(command)) + b'\xAA'
        self.ser.write(packet)
        return packet
    ## Response Packet Structure
    # SOP : 0x55
    # Data Field  : 16 bytes
    # Checksum : 1 byte
    # EOP : 0xAA
    def __readResponseRunner(self):
        while True:
            try:
                if self.ser.in_waiting:
                    if self.ser.read() == b'\x55':
                        data = self.ser.read(16)
                        checksum = self.ser.read()
                        eop = self.ser.read()
                        responseID = data[0]
                        self.__response[responseID] = data
            except Exception as e:
                self.esp_msg = "Comm Error"
                time.sleep(0.5) # wait as we try to reconnect back

    def getResponse(self, responseID):
        return self.__response.get(responseID)
    def hardTare(self):
        self.sendCommand(commandSetBias(True))
    def softTare(self):
        self.offsetFx, self.offsetFy, self.offsetFz, self.offsetTx, self.offsetTy, self.offsetTz, _ = responseReadFTData(self.getResponse(ID_START_FT_DATA_OUTPUT))
    def getTareFT(self):
        rawFx, rawFy, rawFz, rawTx, rawTy, rawTz, _ = responseReadFTData(self.getResponse(ID_START_FT_DATA_OUTPUT))
        data = np.array([rawFx - self.offsetFx, rawFy - self.offsetFy, rawFz - self.offsetFz, rawTx - self.offsetTx, rawTy - self.offsetTy, rawTz - self.offsetTz])
        return data
    
    def init_rft(self):
        self.sendCommand(COMMAND_STOP_FT_DATA_OUTPUT)
        time.sleep(0.1)
        self.ser.flush()

        self.sendCommand(COMMNAD_READ_MODEL_NAME)
        time.sleep(0.1)
        self.sendCommand(COMMAND_READ_SERIAL_NUMBER)
        time.sleep(0.1)
        print("RFT Name:"+responseReadModelName(self.getResponse(ID_READ_MODEL_NAME))+" \tSerial #:"+responseReadSerialNUmber(self.getResponse(ID_READ_SERIAL_NUMBER)))

        # set and read baud rate
        self.sendCommand(commandSetBaudrate(115200))
        time.sleep(1) # give more than 1 second to set baud rate
        self.sendCommand(COMMAND_READ_BAUDRATE)
        time.sleep(0.1)
        print(f"RFT Response:{responseSetBaudrate(self.getResponse(ID_SET_BAUDRATE))} \t\tCurrent Baud Rate:{responseReadBaudrate(self.getResponse(ID_READ_BAUDRATE))}")

        # set and read output rate
        self.sendCommand(commandSetDataOutputRate(100))
        time.sleep(1)
        self.sendCommand(COMMAND_READ_DATA_OUTPUT_RATE)
        time.sleep(0.1)
        print(f"RFT Response:{responseSetDataOutputRate(self.getResponse(ID_SET_DATA_OUTPUT_RATE))} \t\tData Output Rate:{responseReadDataOutputRate(self.getResponse(ID_READ_DATA_OUTPUT_RATE))}")

        # start RFT 
        self.sendCommand(COMMAND_START_FT_DATA_OUTPUT)
        time.sleep(0.1)
        print(f"RFT Start: {responseReadFTData(self.getResponse(ID_START_FT_DATA_OUTPUT))}")
        self.sendCommand(commandSetFilter(1,10))
        time.sleep(0.1)
        self.hardTare()
        time.sleep(0.1)
        self.softTare()

if __name__ == "__main__":
    p = RFTSeriesServer()
