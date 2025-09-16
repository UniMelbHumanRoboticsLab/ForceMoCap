import serial
import time
import sys,os
import pickle as pkl

import numpy as np
np.set_printoptions(
    precision=4,
    linewidth=np.inf,   
    formatter={'float_kind': lambda x: f"{x:.4f}"}
)
from PySide6.QtCore import QObject, QThread, Signal,QTimer,Slot,QElapsedTimer,Qt, QMetaObject
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget

class ESPSerial(QObject):
    forces_ready = Signal(list)
    stopped = Signal()
    def __init__(self, port="COM9", baud=9600,side="left"):
        super().__init__()
        self.port = port
        self.baud = baud
        self.side = side
        
        # get the calibration matrices for each sensor
        self.esp_data_arr = np.zeros((8,1))
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
    UART Connection Functions
    """
    def reconnect(self):
        while True:
            try:
                self.ser = serial.Serial(self.port, self.baud)
                break
            except Exception as e:
                print(e)
                time.sleep(1)
    def close(self):
        self.ser.close()
        self.esp_msg = "Unknown"
        self.esp_data_arr = np.zeros((8,1))
    def restart(self):
        self.close()
        self.reconnect()

    """
    ESP Force Helper Function and Callback
    """
    def get_latest(self):
        self.ser.reset_input_buffer() # refresh the serial buffer
        self.esp_data = self.ser.readline().decode('utf-8', errors='ignore').strip()
        self.esp_data_parsed = (self.esp_data[1:-1]).split("\t")
    def read_esp_data(self):
        # print(0)
        try:
            self.get_latest()
            while (self.esp_data == '' or self.esp_data[0] != 's' or len(self.esp_data_parsed)<=1 or len(self.esp_data_parsed)>9):
                # print("Caught:",len(self.esp_data_parsed),self.esp_data,self.esp_data[0])
                self.get_latest()                

            esp_data_arr = np.round(np.array(self.esp_data_parsed,dtype=float),3)            
        except Exception as e:
            self.esp_msg = "Comm Error"
            print(self.esp_data)
            print(e)
            time.sleep(0.5) # wait as we try to reconnect back

        # calibration regression
        force_data = []
        for esp_data,calib_matrix in zip(esp_data_arr,self.calib_matrices):
            if esp_data < 0.01:
                conductance = 0
            else:
                conductance = 1/esp_data*1000
            force = calib_matrix.predict(np.array([[conductance]]))
            force_data.append(force[0])
        force_data = np.array(force_data)
        # palm_force = np.sum(force_data[5:])
        # hand_force = np.append(np.array(palm_force),force_data[:5])

        # update FPS
        self.esp_frame_count += 1
        self.esp_cur_time = self.esp_timer.elapsed()
        if self.esp_cur_time-self.esp_last_time >= 500:
            self.esp_fps = self.esp_frame_count * 1000 / (self.esp_cur_time-self.esp_last_time)
            self.esp_last_time = self.esp_cur_time
            self.esp_frame_count = 0
        self.forces_ready.emit([force_data,self.esp_fps])

    """
    Initialization Callback
    """
    def start_worker(self):
        self.reconnect()
        
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.read_esp_data)
        self.poll_timer.start(int(1/150*1000))

        print(f"{self.side} ESP Started")

    """
    External Signal Callback
    """
    @Slot()
    def stop(self):
        self.close()
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
        self.worker = ESPSerial()
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.readResponseRunner)
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
    sys.exit(app.exec_())