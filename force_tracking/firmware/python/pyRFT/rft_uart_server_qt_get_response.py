import serial
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

class RFTSerial(QObject):
    forces_ready = Signal(dict)
    stopped = Signal()

    def __init__(self, port="COM5", baud=115200):
        super().__init__()

        self.port = port
        self.port = port
        self.baud = baud
        self.rft_data_arr = np.zeros((7,1))
        self.response = dict()
        self.rft_pose = SE3()
        self.update_rate = 100

        # init FPS
        self.rft_timer = QElapsedTimer() # use the system clock
        self.rft_timer.start()
        self.rft_frame_count = 0
        self.rft_fps = 0
        self.rft_cur_time = self.rft_timer.elapsed()
        self.rft_last_time = self.rft_timer.elapsed()

    def reconnect(self):
        while True:
            try:
                self.ser = serial.Serial(self.port, self.baud)
                break
            except Exception as e:
                print(e)
                time.sleep(0.3)
    def close(self):
        self.ser.flush()
        self.ser.close()
        self.on = False
    def restart(self):
        self.close()
        self.reconnect()
        self.on = True

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
                # read serial until encounter start byte
                print("Stuck")
                pass

            data = self.ser.read(16)
            checksum = self.ser.read()
            eop = self.ser.read()
            received_response_id = data[0]
            self.response[responseID] = data

            # resend command if incorrect response ID
            if received_response_id != responseID:
                print(f"Resend {responseID}")
                self.sendCommand(cmd)
        return data
    
    def hardTare(self):
        self.sendCommand(commandSetBias(True))
        time.sleep(0.2)
    def softTare(self):
        self.sendCommand(COMMAND_READ_FT_DATA)
        self.offsetFx, self.offsetFy, self.offsetFz, self.offsetTx, self.offsetTy, self.offsetTz, overload = responseReadFTData(self.getResponse(ID_READ_FT_DATA,COMMAND_READ_FT_DATA))
        return [self.offsetFx, self.offsetFy, self.offsetFz, self.offsetTx, self.offsetTy, self.offsetTz, overload]
    def getTareFT(self):
        self.sendCommand(COMMAND_READ_FT_DATA)
        rawFx, rawFy, rawFz, rawTx, rawTy, rawTz, _ = responseReadFTData(self.getResponse(ID_READ_FT_DATA,COMMAND_READ_FT_DATA))
        data = np.array([rawFx - self.offsetFx, rawFy - self.offsetFy, rawFz - self.offsetFz, rawTx - self.offsetTx, rawTy - self.offsetTy, rawTz - self.offsetTz])
        return data
    def init_rft(self):
        print("\nInitialize RFT")

        # set and read baud rate
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

        # set and read filter settings
        filter_cmd = self.sendCommand(commandSetFilter(1,6))
        filter_response = responseSetFilter(self.getResponse(ID_SET_FILTER,filter_cmd))
        time.sleep(0.2)
        filter2_cmd = self.sendCommand(COMMAND_READ_FILTER)
        filter2_response = responseReadFilter(self.getResponse(ID_READ_FILTER,filter2_cmd))
        print(f"RFT Response:{filter_response} \t\tFilter Settings:{filter2_response}")

        print()
        print(f"Soft Bias:{self.softTare()}")
        self.ser.reset_input_buffer()

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
    @Slot()
    def stop(self):
        self.ser.close()
        self.poll_timer.stop()
        self.stopped.emit()
        
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
        self.label.setText(f'info: {text["rft_fps"]},{text["rft_data_arr"]}')

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