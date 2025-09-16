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
        # self.wait_calibrate()
        self.esp_data_arr = np.zeros((8,1))

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
        self.esp_msg = "Unknown"
        self.esp_data_arr = np.zeros((8,1))
    def restart(self):
        self.close()
        self.reconnect()
        self.on = True
    def get_latest(self):
        self.ser.reset_input_buffer() # refresh the serial buffer
        return self.ser.readline().decode('utf-8', errors='ignore').strip()
    def __readResponseRunner(self):
        while True:
            try:
                self.esp_data = self.get_latest()
                while (self.esp_data == '' or self.esp_data[0] != '\x02' or len(self.esp_data)<=1):
                    self.esp_data = self.get_latest()
                esp_data_parsed = self.esp_data[1:].split("\t")
                with self._lock:
                    self.esp_data_arr = np.round(np.array(esp_data_parsed,dtype=float),3)
            except Exception as e:
                self.esp_msg = "Comm Error"
                time.sleep(0.5) # wait as we try to reconnect back
    
    def get_fsr_data(self):
        with self._lock:
            return self.esp_data_arr
        
if __name__ == "__main__":
    # esp = EspUDPServer()
    # while True:
    #     p = 0

    from blessed import Terminal
    term = Terminal()

    with term.fullscreen():
        # xsens = XSENSServer()
        # vive = OpenVRServer()
        # esp = ESPSeriesServer();
        esp = ESPSeriesServer(port="COM9")
        while True:
            data = esp.get_fsr_data()
            # if response != None:
            print(term.move(1, 0) + term.clear_eos() + f"{data}")