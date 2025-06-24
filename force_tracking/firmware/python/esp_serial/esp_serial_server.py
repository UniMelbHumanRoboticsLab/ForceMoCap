import serial
import time
import threading
import numpy as np

class ESPSeriesServer:
    def __init__(self, port, baud=115200):
        self.port = port
        self.baud = baud
        self.reconnect()
        self.restart() # refresh the esp
        self.wait_calibrate()
        self.esp_data_arr = np.zeros((1,3))

        self.__thread = threading.Thread(target=self.__readResponseRunner)
        self.__thread.daemon = True
        self._lock = threading.Lock()
        self.__thread.start()

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
        self.on = False
        self.calibrated = False
        self.esp_msg = "Unknown"
        self.esp_data_arr = np.zeros((1,3))
    def restart(self):
        self.close()
        self.reconnect()
        self.on = True
    def wait_calibrate(self):
        self.ser.reset_input_buffer()
        print("\nCalibrate ESP")
        while True:
            try:
                # if self.ser.in_waiting:
                #     # self.ser.reset_input_buffer() # refresh the serial buffer
                self.esp_msg = self.ser.readline().decode('utf-8', errors='ignore').strip()
                print(self.esp_msg)
                if self.esp_msg == "Sensors Calibrated" and not self.calibrated:
                    self.calibrated = True
                    break
            except:
                self.esp_msg = "Comm Error"
                print(self.esp_msg)
    def __readResponseRunner(self):
        while True:
            try:
                if self.calibrated:
                    self.ser.reset_input_buffer() # refresh the serial buffer
                    self.esp_data = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    while (self.esp_data == '' or self.esp_data[0] != '\x02' or len(self.esp_data)<=1):
                        self.esp_data = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    esp_data_parsed = self.esp_data[1:].split("\t")
                    with self._lock:
                        self.esp_data_arr = np.round(np.array(esp_data_parsed,dtype=float),3)
            except Exception as e:
                self.esp_msg = "Comm Error"
                time.sleep(0.5) # wait as we try to reconnect back
    
    def get_mlx_data(self):
        with self._lock:
            return self.esp_data_arr