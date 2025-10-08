import socket
import time
import sys,os
import pickle as pkl

import numpy as np
np.set_printoptions(
    precision=4,
    linewidth=np.inf,   
    formatter={'float_kind': lambda x: f"{x:.4f}"}
)

from PySide6.QtCore import QObject, QThread, Signal,QTimer,Slot,QElapsedTimer, Qt, QMetaObject
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget


class ESPUdp(QObject):
    forces_ready = Signal(dict)
    stopped = Signal()
    def __init__(self, ip="192.168.153.121",server_port=4213, port=4211,side="right"):
        super().__init__()
        self.port = port
        self.ip = ip
        self.side = side
        self.server_port = server_port


        # get the calibration matrices for each sensor
        self.esp_data_arr = np.zeros((9,1))
        self.calib_matrices = []
        sensor_list = ["f1","f2","f3","f4","f5","p1","p2","p3","p4"]
        for sensor in sensor_list: # nine sensors per esp, load the calibration_matrices
            calib_path = os.path.join(f"./sensor_calib_fsr/data/{side}/{sensor}", f"model_{side}_{sensor}.pkl")
            with open(calib_path,'rb') as f:
                # print(f"Loading {calib_path}")
                calib_matrix = pkl.load(f)
                self.calib_matrices.append(calib_matrix)
        
        # FPS Calculator
        self.esp_timer = QElapsedTimer() # use the system clock
        self.esp_timer.start()
        self.esp_frame_count = 0
        self.esp_fps = 0
        self.esp_cur_time = self.esp_timer.elapsed()
        self.esp_last_time = self.esp_timer.elapsed()

    """
    UDP Connection Functions
    """
    def reconnect(self):
        print("ESP Connecting")
        try:
            # Create a socket object
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('', self.server_port)) # replace the ip with ''
            self.server_socket.sendto(bytes("HI", "utf-8"), (self.ip, self.port))
        except Exception as e:
            print(e)
            time.sleep(1)
        while self.server_socket.recvfrom(255)[0].decode().strip() != "HI":
            print("Waiting ESP Response")
        print(self.get_latest())
        print("ESP Connected")
    def close(self):
        self.esp_msg = "Unknown"
        self.esp_data_arr = np.zeros((9,1))
    def restart(self):
        self.close()
        self.reconnect()
        self.on = True

    """
    ESP Force Helper Function and Callback
    """
    def get_latest(self):
        self.esp_data = self.server_socket.recvfrom(130)[0].decode().strip()
        self.esp_data_parsed = (self.esp_data[1:]).split("\t")
        self.esp_data_parsed = np.array(self.esp_data_parsed, dtype=float)
    def read_esp_data(self):
        try:
            # update FPS
            self.esp_frame_count += 1
            self.esp_cur_time = self.esp_timer.elapsed()
            if self.esp_cur_time-self.esp_last_time >= 500:
                self.esp_fps = self.esp_frame_count * 1000 / (self.esp_cur_time-self.esp_last_time)
                self.esp_last_time = self.esp_cur_time
                self.esp_frame_count = 0

            self.get_latest()
            while (self.esp_data == '' or self.esp_data[0] != 's' or len(self.esp_data_parsed)<=1 or len(self.esp_data_parsed)>9):
                print("Caught:",len(self.esp_data_parsed),self.esp_data,self.esp_data[0])
                self.get_latest()                
            esp_data_arr = np.round(self.esp_data_parsed,3)    
                    
            # calibration regression
            force_data = []
            for esp_data,calib_matrix in zip(esp_data_arr,self.calib_matrices):
                # if esp_data < 0.01:
                #     conductance = 0
                # else:
                #     conductance = 1/esp_data*1000
                conductance = esp_data
                force = calib_matrix.predict(np.array([[conductance]]))
                if force[0] < 0:
                    force[0] = 0
                force_data.append(force[0])
            force_data = np.array(force_data)
            
            data = {
                "force_data":force_data,
                "raw_data":esp_data_arr,
                "esp_fps":self.esp_fps,
            }
            self.forces_ready.emit(data)
        except Exception as e:
            data = {
                "force_data":np.array([0,0,0,0,0,0,0,0,0]),
                "esp_fps":self.esp_fps
            }
            data = {
                "force_data":np.array([0,0,0,0,0,0,0,0,0]),
                "raw_data":np.array([0,0,0,0,0,0,0,0,0]),
                "esp_fps":self.esp_fps,
            }
            self.forces_ready.emit(data)

    """
    Initialization Callback
    """
    def start_worker(self):  
        self.reconnect()
        self.poll_timer = QTimer()
        self.poll_timer.setTimerType(Qt.PreciseTimer)
        self.poll_timer.timeout.connect(self.read_esp_data)
        self.poll_timer.start(int(1/150*1000))
        print(f"{self.side} ESP Started")
    
    """
    External Signals Callback
    """
    @Slot()
    def stop(self):
        self.server_socket.sendto(bytes("STOP", "utf-8"), (self.ip, self.port))
        self.server_socket.close()
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
        self.worker = ESPUdp()
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.start_worker)
        self.worker.forces_ready.connect(self.update_label)
        self.button.clicked.connect(self.cleanup)

        self.thread.start()

    def update_label(self, text):
        self.label.setText(f"info: {text}")

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