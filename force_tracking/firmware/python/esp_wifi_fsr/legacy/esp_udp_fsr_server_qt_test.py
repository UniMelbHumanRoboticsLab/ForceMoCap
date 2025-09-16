import socket
import time
import sys,os
import pickle as pkl

import numpy as np
np.set_printoptions(
    precision=4,
    linewidth=np.inf,   
    formatter={'float_kind': lambda x: f"{x:.4f}"})

from PySide6.QtCore import QObject, QThread, Signal,QTimer,Slot,QElapsedTimer, Qt, QMetaObject
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget

class ESPUdpReader(QObject):
    msg_ready = Signal(list)
    def __init__(self, ip="127.0.0.1", port=9004):
        super().__init__()
        self.ip = ip
        self.port = port
        self.buffer_message = ""

    """
    UDP Connection Functions
    """
    def reconnect(self):
        while True:
            try:
                # Create a socket object
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
                self.server_socket.bind(('', 4212)) # replace the ip with ''
                self.server_socket.sendto(bytes("HI", "utf-8"), (self.ip, self.port))
                break
            except Exception as e:
                print(e)
                time.sleep(1)
        while self.server_socket.recvfrom(255)[0].decode().strip() != "HI":
            print("Waiting ESP Response")
    
    def get_latest(self):
        self.esp_data = self.server_socket.recvfrom(130)[0].decode().strip()
        self.esp_data_parsed = (self.esp_data[1:]).split("\t")
        self.esp_data_parsed = np.array(self.esp_data_parsed, dtype=float)
    def updateResponse(self):
        self.get_latest()  
        # while (self.esp_data == '' or self.esp_data[0] != 's' or len(self.esp_data_parsed)<=1 or len(self.esp_data_parsed)>9):
        #     print("Caught:",len(self.esp_data_parsed),self.esp_data,self.esp_data[0])
        #     self.get_latest()  
        if (self.esp_data != '' and self.esp_data[0] == 's' and len(self.esp_data_parsed)==9):
            self.msg_ready.emit([self.esp_data_parsed])

    def start_worker(self):
        self.reconnect()
        self.esp_response_timer = QTimer()
        self.esp_response_timer.setTimerType(Qt.PreciseTimer)
        self.esp_response_timer.timeout.connect(self.updateResponse)
        self.esp_response_timer.start(5)
    @Slot()
    def close(self):
        self.esp_response_timer.stop()

class ESPUdp(QObject):
    forces_ready = Signal(dict)
    stopped = Signal()
    def __init__(self, ip="192.168.170.121", port=4211,side="left"):
        super().__init__()
        self.port = port
        self.ip = ip
        self.side = side

        # get the calibration matrices for each sensor
        self.esp_data_arr = np.zeros((9,1))
        self.calib_matrices = []
        sensor_list = ["f1","f2","f3","f4","f5","p1","p2","p3","p4"]
        for sensor in sensor_list: # nine sensors per esp, load the calibration_matrices
            calib_path = os.path.join(f"./sensor_calib_fsr/data/{side}/{sensor}", f"model.pkl")
            with open(calib_path,'rb') as f:
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
    ESP Force Helper Function and Callback
    """
    def read_esp_data(self):
        try:
            esp_data_arr = np.round(self.esp_data_parsed,3) 
            # calibration regression
            force_data = []
            for esp_data,calib_matrix in zip(esp_data_arr,self.calib_matrices):
                if esp_data < 0.01:
                    conductance = 0
                else:
                    conductance = 1/esp_data*1000
                force = calib_matrix.predict(np.array([[conductance]]))
                # force = [conductance]
                force_data.append(force[0])
            force_data = np.array(force_data)

            # update FPS
            self.esp_frame_count += 1
            self.esp_cur_time = self.esp_timer.elapsed()
            if self.esp_cur_time-self.esp_last_time >= 1000:
                self.esp_fps = self.esp_frame_count * 1000 / (self.esp_cur_time-self.esp_last_time)
                self.esp_last_time = self.esp_cur_time
                self.esp_frame_count = 0
            
            data = {
                "force_data":force_data,
                "esp_fps":self.esp_fps
            }
            self.forces_ready.emit(data)
        except Exception as e:
            self.esp_msg = "Comm Error"
            self.esp_cur_time = self.esp_timer.elapsed()
            self.esp_last_time = self.esp_timer.elapsed()
            # print(e)
            # time.sleep(0.5) # wait as we try to reconnect back


    """
    Initialization Callback
    """
    def start_worker(self):  
        # create a thread and worker that updates and reads the buffer quickly
        self.reader_thread = QThread()
        self.reader_worker = ESPUdpReader(self.ip, self.port)
        # # Connect signals from reader thread and worker to rft thread and worker
        self.reader_thread.started.connect(self.reader_worker.start_worker)
        self.reader_worker.msg_ready.connect(self.update_response)
        # Connect ss stop to stop reader
        self.stopped.connect(self.reader_worker.close)
    
        self.poll_timer = QTimer()
        self.poll_timer.setTimerType(Qt.PreciseTimer)
        self.poll_timer.timeout.connect(self.read_esp_data)
        self.poll_timer.start(int(1/100*1000))
        
        self.reader_thread.start()
        print(f"{self.side} ESP Started")
    """
    External Signals Callback
    """
    @Slot(list)
    def update_response(self,worker_response):
         self.esp_data_parsed = worker_response[0]
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