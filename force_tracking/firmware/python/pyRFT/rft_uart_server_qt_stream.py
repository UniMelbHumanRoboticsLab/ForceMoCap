import serial
import time
import sys,os
sys.path.append(os.path.join(os.path.dirname(__file__)))
from rft_helper.RFT_UART_command import *
from rft_helper.RFT_UART_response import * 

import numpy as np
np.set_printoptions(
    precision=4,
    linewidth=np.inf,   
    formatter={'float_kind': lambda x: f"{x:.4f}"}
)
from scipy.spatial.transform import Rotation as R
from spatialmath import SE3

from PySide6.QtCore import QObject, QThread, Signal,QTimer,Slot,QElapsedTimer, Qt, QMetaObject
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget
import debugpy

class RFTSerialReader(QObject):
    msg_ready = Signal(list)
    def __init__(self, port="COM5", baud=115200):
        super().__init__()
        self.port = port
        self.baud = baud

    def reconnect(self):
        while True:
            try:
                self.ser = serial.Serial(self.port, self.baud)
                break
            except Exception as e:
                print(e)
                time.sleep(0.3)

    def sendCommand(self, command):
        if len(command) != 8:
            raise ValueError('Data field must be 8 bytes long')
        packet = b'\x55' + command + int.to_bytes(sum(command)) + b'\xAA'
        self.ser.write(packet)
        return command
    
    def updateResponse(self):
        if self.ser.in_waiting:
            if self.ser.read() == b'\x55':
                data = self.ser.read(16)
                checksum = self.ser.read()
                eop = self.ser.read()
                responseID = data[0]
                self.msg_ready.emit(["ready",data])
            else:
                self.msg_ready.emit(["not ready",b'\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55'])
                self.ser.reset_input_buffer()

    def start_worker(self):
        self.rft_response_timer = QTimer()
        self.rft_response_timer.setTimerType(Qt.PreciseTimer)
        self.rft_response_timer.timeout.connect(self.updateResponse)
        self.rft_response_timer.start(2)
        self.reconnect()
    
    @Slot()
    def close(self):
        self.ser.flush()
        self.sendCommand(COMMAND_STOP_FT_DATA_OUTPUT)
        time.sleep(0.2)
        self.ser.close()  
        self.rft_response_timer.stop()

    @Slot()
    def clear_buffer(self):
        self.rft_response_timer.stop()
        self.ser.flush()
        self.sendCommand(COMMAND_STOP_FT_DATA_OUTPUT)
        time.sleep(0.2)
        while self.ser.in_waiting:
            self.ser.reset_input_buffer()
            print("Cleaning RFT")
            time.sleep(1)
        print("CLEARED RFT BUFFER")
        self.ser.flush()
        self.sendCommand(COMMAND_START_FT_DATA_OUTPUT)
        time.sleep(1)
        self.rft_response_timer.start()
        self.msg_ready.emit(["not ready",b'\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55'])

class RFTSerial(QObject):
    forces_ready = Signal(dict)
    stopped = Signal()
    
    def __init__(self, port="COM14", baud=115200):
        super().__init__()

        self.port = port
        self.baud = baud
        self.rft_data_arr = np.zeros((7,1))
        self.rft_response = dict()
        self.rft_pose = SE3()
        self.update_rate = 100

        # FPS Calculator
        self.rft_timer = QElapsedTimer() # use the system clock
        self.rft_timer.start()
        self.rft_frame_count = 0
        self.rft_fps = 0
        self.rft_cur_time = self.rft_timer.elapsed()
        self.rft_last_time = self.rft_timer.elapsed()

        # create a thread and worker that updates and reads the buffer quickly
        self.reader_thread = QThread()
        self.reader_worker = RFTSerialReader(self.port, self.baud)
        # # Connect signals from reader thread and worker to rft thread and worker
        self.reader_thread.started.connect(self.reader_worker.start_worker)
        self.reader_worker.msg_ready.connect(self.update_response)
        # Connect rft stop to stop reader
        self.stopped.connect(self.reader_worker.close)

    """
    UART Connection Functions
    """
    def reconnect(self):
        while True:
            try:
                self.ser = serial.Serial(self.port, self.baud)
                break
            except Exception as e:
                print(e)
                time.sleep(0.3)     
    def restart(self):
        self.reconnect()

    """
    UART Helper Function
    """
    def sendCommand(self, command):
        if len(command) != 8:
            raise ValueError('Data field must be 8 bytes long')
        packet = b'\x55' + command + int.to_bytes(sum(command)) + b'\xAA'
        self.ser.write(packet)
        return command
    def getResponse(self, responseID,cmd=COMMAND_START_FT_DATA_OUTPUT):
        received_response_id = 0
        while received_response_id != responseID:
            
            start = self.ser.read()
            while start != b'\x55':
                start = self.ser.read()
                print("Stuck")
                pass

            data = self.ser.read(16)
            checksum = self.ser.read()
            eop = self.ser.read()
            received_response_id = data[0]
            self.rft_response[responseID] = data

            # resend command if incorrect response ID
            if received_response_id != responseID: 
                self.sendCommand(cmd)
        return data   

    """
    RFT Force Helper Function and Callback
    """
    def hardTare(self):
        self.sendCommand(commandSetBias(True))
        time.sleep(0.2)
    def softTare(self):
        self.sendCommand(COMMAND_READ_FT_DATA)
        self.offsetFx, self.offsetFy, self.offsetFz, self.offsetTx, self.offsetTy, self.offsetTz, overload = responseReadFTData(self.getResponse(ID_READ_FT_DATA,COMMAND_READ_FT_DATA))
        return [self.offsetFx, self.offsetFy, self.offsetFz, self.offsetTx, self.offsetTy, self.offsetTz, overload]
    def getTareFT(self):
        rawFx, rawFy, rawFz, rawTx, rawTy, rawTz, _ = responseReadFTData(self.rft_response[ID_START_FT_DATA_OUTPUT])
        data = np.array([rawFx - self.offsetFx, rawFy - self.offsetFy, rawFz - self.offsetFz, rawTx - self.offsetTx, rawTy - self.offsetTy, rawTz - self.offsetTz])
        return data
    def read_rft_data(self):
        # update FPS
        self.rft_frame_count += 1
        self.rft_cur_time = self.rft_timer.elapsed()
        if self.rft_cur_time-self.rft_last_time >= 500:
            self.rft_fps = self.rft_frame_count * 1000 / (self.rft_cur_time-self.rft_last_time)
            self.rft_last_time = self.rft_cur_time
            self.rft_frame_count = 0

        self.rft_data_arr = self.getTareFT()

        data = {
            "rft_data_arr":self.rft_data_arr,
            "rft_pose":self.rft_pose,
            "rft_fps":self.rft_fps
        }
        self.forces_ready.emit(data)

    """
    Initialization Callback
    """
    def init_rft(self):
        print("\nInitialize RFT")

        # set and read baud rate
        self.baud = 115200
        br_cmd = self.sendCommand(commandSetBaudrate(self.baud))
        br_response = responseSetBaudrate(self.getResponse(ID_SET_BAUDRATE,br_cmd))
        time.sleep(0.2)
        br2_cmd = self.sendCommand(COMMAND_READ_BAUDRATE)
        br2_response = responseReadBaudrate(self.getResponse(ID_READ_BAUDRATE,br2_cmd))
        print(f"RFT Response:{br_response} \t\tCurrent Baud Rate:{br2_response}")

        name_cmd = self.sendCommand(COMMAND_READ_MODEL_NAME)
        name_response = responseReadModelName(self.getResponse(ID_READ_MODEL_NAME,name_cmd))
        time.sleep(0.2)
        serial_num_cmd = self.sendCommand(COMMAND_READ_SERIAL_NUMBER)
        ser_num_response = responseReadSerialNUmber(self.getResponse(ID_READ_SERIAL_NUMBER,serial_num_cmd))
        print("RFT Name:"+name_response+" \tSerial #:"+ser_num_response)

        # set and read output rate
        dor_cmd = self.sendCommand(commandSetDataOutputRate(self.update_rate))
        dor_response = responseSetDataOutputRate(self.getResponse(ID_SET_DATA_OUTPUT_RATE,dor_cmd))
        time.sleep(0.2)
        dor2_cmd = self.sendCommand(COMMAND_READ_DATA_OUTPUT_RATE)
        dor2_response = responseReadDataOutputRate(self.getResponse(ID_READ_DATA_OUTPUT_RATE,dor2_cmd))
        print(f"RFT Response:{dor_response} \t\tData Output Rate:{dor2_response}")

        # set and read filter settings
        filter_cmd = self.sendCommand(commandSetFilter(1,6))
        filter_response = responseSetFilter(self.getResponse(ID_SET_FILTER,filter_cmd))
        time.sleep(0.2)
        filter2_cmd = self.sendCommand(COMMAND_READ_FILTER)
        filter2_response = responseReadFilter(self.getResponse(ID_READ_FILTER,filter2_cmd))
        print(f"RFT Response:{filter_response} \t\tFilter Settings:{filter2_response}")
        
        # set bias in RFT 
        start_cmd = self.sendCommand(COMMAND_START_FT_DATA_OUTPUT)
        time.sleep(0.2)
        self.hardTare()
        responseReadFTData(self.getResponse(ID_START_FT_DATA_OUTPUT))
        self.sendCommand(COMMAND_STOP_FT_DATA_OUTPUT)
        time.sleep(2)

        print(f"Soft Bias:{self.softTare()}")
        self.ser.reset_input_buffer()
        self.sendCommand(COMMAND_START_FT_DATA_OUTPUT)
        self.ser.close() # let the reader work take over the serial port
    def start_worker(self):        
        self.reconnect()
        self.sendCommand(COMMAND_STOP_FT_DATA_OUTPUT)
        time.sleep(2)
        self.ser.flush()

        self.init_rft()
        self.poll_timer = QTimer()
        self.poll_timer.setTimerType(Qt.PreciseTimer)
        self.poll_timer.timeout.connect(self.read_rft_data)
        self.poll_timer.start(int(1/self.update_rate*1000))

        self.reader_thread.start()
        print(f"RFT Started\n")

    """
    External Signal Callbacks
    """
    @Slot(list)
    def update_pose(self,vive_response):
        cur_marker_pos = vive_response["trackers_pos"][0] # position of sensor in inertial frame - take the first one
        cur_marker_frame = R.from_quat(vive_response["trackers_frame"][0]).as_matrix()
        T = np.eye(4,4)
        T[:3,:3] = cur_marker_frame
        T[:3, 3] = cur_marker_pos
        self.rft_pose = SE3(T)
    @Slot(list)
    def update_response(self,worker_response):
         if worker_response[0] == "ready":
            self.rft_response[ID_START_FT_DATA_OUTPUT] = worker_response[1]
         else:
            self.rft_response[ID_START_FT_DATA_OUTPUT] = b'\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55\x55'
            print(worker_response[0])
    @Slot()
    def stop(self):
        self.poll_timer.stop()
        self.stopped.emit()
        self.reader_thread.terminate()   
        
# ----------------------------
# Main application window
# ----------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QThread Example")
        
        # Label to display data
        self.label = QLabel("Waiting for data...")
        self.button = QPushButton("Stop Thread")

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Setup thread and worker
        self.thread = QThread()
        self.worker = RFTSerial()
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.start_worker)
        self.worker.forces_ready.connect(self.update_label)
        self.button.clicked.connect(self.cleanup)

        self.thread.start()

    def update_label(self, text):
        self.label.setText(f"info: {text[0]},{text[2]}")

    def cleanup(self):
        QMetaObject.invokeMethod(self.worker, "stop", Qt.ConnectionType.QueuedConnection)
        self.worker.stopped.connect(self.thread.exit)
        self.label.setText("Thread stopped.")

        import time
        time.sleep(0.3) 
        self.close()

# ----------------------------
# Application entry point
# ----------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())