import os, sys,json

from fmc_calib_logger import FMCLoggerCalib

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from base.fmc_base import FMCBase

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from firmware.python.esp_serial_mlx.esp_serial_mlx_server_qt import ESPSerial
from firmware.python.pyRFT.rft_uart_server_qt_get_response import RFTSerial

import numpy as np
from scipy.spatial.transform import Rotation as R
from PySide6 import QtWidgets
from PySide6.QtGui import QShortcut
from PySide6.QtCore import QThread,Qt,QMetaObject,Slot

class FMCCalibMLX(FMCBase):
    def __init__(self,init_args):
        self.init_args = init_args
        self.gui_3d_on = self.init_args["init_flags"]["gui_3d_on"]
        self.force_gui = self.init_args["init_flags"]["force_gui"]
        self.num_closed_threads = 0
        self.num_opened_threads = 0

        super().__init__(freq=self.init_args["gui_freq"],gui_3d_on=self.gui_3d_on)

        if self.force_gui["on?"]:
            if self.force_gui["ESP"] or self.force_gui["RFT"]:
                self.force_mag_live_stream = self.init_live_stream(num_columns=3)
            
        """
        Initilization
        """
        self.init_sensors()
        self.init_shortcuts()

    """
    Init Sensor Worker / Thread / GUI Helper Functions
    """
    def add_opened_threads(self):
        self.num_opened_threads += 1
        print(f"Threads Opened:{self.num_opened_threads}")
    def init_esp_sensor(self):
        sides = self.init_args["ESP"]["sides"]
        ports = self.init_args["ESP"]["ports"]
        self.force_modules = {}
        
        for side,port in zip(sides,ports):
            force_module = {}
            # init response label
            force_module["response_label"] = self.init_response_label(size=[500,50])
            # init esp thread and worker
            esp_thread = QThread()
            esp_worker = ESPSerial(port=port,side=side)
            force_module["sensor"] = {"thread":esp_thread,
                                      "worker":esp_worker}
            # init esp live stream plot
            if self.force_gui["on?"] and self.force_gui["ESP"]:
                force_module["live_stream_plots"] = self.add_live_stream_plot(live_stream=self.force_mag_live_stream,sensor_name= f"ESP",unit="N",dim=3)
            self.force_modules[f"{side}"] = force_module
    def init_rft_sensor(self):
        # init response label
        self.rft_label = self.init_response_label(size=[500,50])
        # init rft thread and worker
        self.rft_thread = QThread()
        self.rft_worker = RFTSerial(port=self.init_args["RFT"])
        # init rft live stream plot
        if self.force_gui["on?"] and self.force_gui["RFT"]:
            self.rft_live_stream_plot = self.add_live_stream_plot(live_stream=self.force_mag_live_stream,sensor_name= f"RFT",unit="N",dim=3)
    def init_logger(self):
        # init response label
        self.logger_label = self.init_response_label(size=[500,150])
        self.logger_thread = QThread()
        self.logger_worker = FMCLoggerCalib(sensor_flags=self.init_args["init_flags"],
                                            side=self.init_args["side"],
                                            finger_id=[self.init_args["finger_name"],self.init_args["finger_id"]],
                                            take_num = self.init_args["take_num"] )
    def init_shortcuts(self):
        # to start / stop logging at button press
        if self.init_args["init_flags"]["log"]  == 1:
            # to start logging
            start_log = QShortcut("S", self)
            start_log.activated.connect(self.logger_worker.start_worker)
            # to stop logging and close everything
            stop_log = QShortcut("C", self)
            stop_log.activated.connect(self.logger_worker.reset_logger)
            stop_log.activated.connect(self.gui_timer.stop)
            
        close = QShortcut("Q", self)
        close.activated.connect(self.gui_timer.stop)
        close.activated.connect(self.close_workers)
    def init_sensors(self):
        """
        Init sensor thread and worker
        """
        if self.init_args["init_flags"]["esp"] == 1:
            self.init_esp_sensor()
        if self.init_args["init_flags"]["rft"] == 1:
            self.init_rft_sensor()
        if self.init_args["init_flags"]["log"] == 1:
            self.init_logger()
            self.logger_response = {
            "print_text":"Idle\n",
            "logger_fps":0.0
        }
        
        """
        Move sensor worker to thread 
        Connect intersensor signals
        Connect signals to sensor GUI callbacks
        Connect thread start to start sensor worker, update number of open threads
        Connect worker stop to stop thread at closeup
        Connect thread finished to close app
        """
        if self.init_args["init_flags"]["esp"]  == 1:
            sides = self.init_args["ESP"]["sides"]
            for side in sides:
                # move worker to thread
                self.force_modules[side]["sensor"]["worker"].moveToThread(self.force_modules[side]["sensor"]["thread"])
                # connect to sensor gui
                self.force_modules[side]["sensor"]["worker"].forces_ready.connect(self.update_esp_response,type=Qt.ConnectionType.QueuedConnection)
                # connect thread start to start worker
                self.force_modules[side]["sensor"]["thread"].started.connect(self.force_modules[side]["sensor"]["worker"].start_worker)
                self.force_modules[side]["sensor"]["thread"].started.connect(self.add_opened_threads)
                # connect worker stop to stop thread at closeup
                self.force_modules[side]["sensor"]["worker"].stopped.connect(self.force_modules[side]["sensor"]["thread"].exit)
                # connect thread finished to close app
                self.force_modules[side]["sensor"]["thread"].finished.connect(self.close_app)
        if self.init_args["init_flags"]["rft"] == 1:
            # move worker to thread
            self.rft_worker.moveToThread(self.rft_thread)
            # connect to sensor gui
            self.rft_worker.forces_ready.connect(self.update_rft,type=Qt.ConnectionType.QueuedConnection)
            # connect thread start to start worker   
            self.rft_thread.started.connect(self.rft_worker.start_worker)
            self.rft_thread.started.connect(self.add_opened_threads)
            # connect worker stop to stop thread at closeup
            self.rft_worker.stopped.connect(self.rft_thread.exit)
            # connect thread finished to close app
            self.rft_thread.finished.connect(self.close_app)
        if self.init_args["init_flags"]["log"]  == 1:
            # move worker to thread
            self.logger_worker.moveToThread(self.logger_thread)
            # connect rft to logger
            if self.init_args["init_flags"]["rft"]  == 1:
                self.rft_worker.forces_ready.connect(self.logger_worker.update_rft,type=Qt.ConnectionType.QueuedConnection)
            # connect esp to logger
            if self.init_args["init_flags"]["esp"]  == 1:
                sides = self.init_args["ESP"]["sides"]
                for side in sides:
                    self.force_modules[side]["sensor"]["worker"].forces_ready.connect(self.logger_worker.update_esp,type=Qt.ConnectionType.QueuedConnection)
            # connect logger to sensor gui
            self.logger_worker.time_ready.connect(self.update_logger,type=Qt.ConnectionType.QueuedConnection)
            # connect thread start to add opened threads  
            self.logger_thread.started.connect(self.add_opened_threads)
            # connect logger finished saving to close workers
            self.logger_worker.finish_save.connect(self.close_workers)
            # connect worker stop to stop thread at closeup
            self.logger_worker.stopped.connect(self.logger_thread.exit)
            # connect thread finished to close app
            self.logger_thread.finished.connect(self.close_app)

        """
        Start threads
        """
        if self.init_args["init_flags"]["esp"]  == 1:
            sides = self.init_args["ESP"]["sides"]
            for side in sides:
                self.force_modules[side]["sensor"]["thread"].start()
                self.force_modules[side]["sensor"]["thread"].setPriority(QThread.Priority.TimeCriticalPriority)
        if self.init_args["init_flags"]["rft"]  == 1:
            self.rft_thread.start()
            self.rft_thread.setPriority(QThread.Priority.TimeCriticalPriority)
        if self.init_args["init_flags"]["log"]  == 1:
            self.logger_thread.start()
            self.logger_thread.setPriority(QThread.Priority.TimeCriticalPriority)
        
    """
    Update Sensor Variable Callbacks
    """
    @Slot(dict)
    def update_esp_response(self,esp_response):
        self.esp_response = esp_response
    @Slot(dict)
    def update_rft(self,rft_response):
        self.rft_response = rft_response
    @Slot(dict)
    def update_logger(self,logger_response):
        self.logger_response = logger_response

    """
    Update Main GUI Helper Functions and Callback
    """
    def update_gui(self):
        super().update_gui()
        if self.force_gui["on?"]:
            # update live stream
            if self.force_gui["RFT"]:
                self.update_live_stream_buffer(live_stream=self.force_mag_live_stream)
            if self.force_gui["ESP"]:
                self.update_live_stream_buffer(live_stream=self.force_mag_live_stream)
        if hasattr(self, 'esp_response'):
            # update esp info
            force_module = self.force_modules[self.init_args["side"]]      
            raw_data = self.esp_response["raw_data"]
            fps = self.esp_response["esp_fps"]
            self.update_response_label(force_module["response_label"],f'FPS:{fps}\n{raw_data}')
            if self.force_gui["on?"] and self.force_gui["ESP"]:
                # update live stream plot
                self.update_live_stream_plot(self.force_mag_live_stream,force_module["live_stream_plots"],raw_data,dim=3)
        if hasattr(self, 'rft_response'):
            # update rft info
            force_data = self.rft_response["rft_data_arr"]
            fps = self.rft_response["rft_fps"]
            self.update_response_label(self.rft_label,f"FPS:{fps}\n{force_data}")
            if self.force_gui["on?"] and self.force_gui["RFT"]:
                self.update_live_stream_plot(self.force_mag_live_stream,self.rft_live_stream_plot,force_data,dim=3)
        if hasattr(self, 'logger_response'):
            print_text = self.logger_response["print_text"]
            fps = self.logger_response["logger_fps"]
            self.update_response_label(self.logger_label,f"{print_text}FPS:{fps}")
    
    """
    Cleanup
    """
    def close_worker_thread(self,worker):
        QMetaObject.invokeMethod(worker, "stop", Qt.ConnectionType.QueuedConnection)
    def close_workers(self):
        if hasattr(self, 'rft_response'):
            self.close_worker_thread(self.rft_worker)
        if hasattr(self, 'esp_response'):
            self.close_worker_thread(self.force_modules[self.init_args["side"]]["sensor"]["worker"])
        if hasattr(self, 'logger_response'):
            self.close_worker_thread(self.logger_worker)
    @Slot()
    def close_app(self):
        self.num_closed_threads += 1
        if self.num_closed_threads == self.num_opened_threads:
            print("Shutting down app...")
            # clear all plots
            for plt in self.plt_items:
                plt.clear()
                plt.deleteLater()
            self.close()
            self.deleteLater()

if __name__ == "__main__":
    try:
        argv = sys.argv[1]
    except:
        argv ={"gui_freq":60,
               "init_flags":{"esp":1,
                             "rft":1,
                             "log":1,
                             "gui_3d_on":False,
                             "force_gui":{"on?":True,"RFT":True,"ESP":True}},
               "side":"left",
               "finger_name":"p4",
               "finger_id":8,
               "take_num":1,
               "RFT":"COM5",
               "ESP":{"sides":["left"],"ports":["COM9"]}}
        
        argv = json.dumps(argv)

    init_args = json.loads(argv)
    app = QtWidgets.QApplication(sys.argv)
    w = FMCCalibMLX(init_args)
    w.setWindowTitle("ForceMoCap")
    w.show()

    import psutil
    p = psutil.Process(os.getpid())
    p.nice(psutil.REALTIME_PRIORITY_CLASS)  # or REALTIME_PRIORITY_CLASS
    sys.exit(app.exec())
        