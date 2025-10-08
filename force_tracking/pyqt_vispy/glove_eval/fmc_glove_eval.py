import os, sys,json
from fmc_eval_logger import FMCEvalLogger
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from base.fmc_base import FMCBase
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from firmware.python.esp_wifi_fsr.esp_udp_fsr_server_qt import ESPUdp
from firmware.python.pyRFT.rft_uart_server_qt_get_response import RFTSerial
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from mo_cap.vive.openvr_server_qt import OpenVRServer
from mo_cap.hand_ss.hand_ss_server_qt import SSHandClient

import numpy as np
from scipy.spatial.transform import Rotation as R


from PySide6 import QtWidgets
from PySide6.QtGui import QShortcut
from PySide6.QtCore import QThread,Qt,QMetaObject,Slot

class FMCGloveEval(FMCBase):
    def __init__(self,init_args):
        self.init_args = init_args
        self.gui_3d_on = self.init_args["init_flags"]["gui_3d_on"]
        self.wrench_gui = self.init_args["init_flags"]["wrench_gui"]
        self.wrench_type = self.init_args["wrench_type"]
        self.num_closed_threads = 0
        self.num_opened_threads = 0

        super().__init__(freq=self.init_args["gui_freq"],gui_3d_on=self.gui_3d_on)

        if self.wrench_gui["on?"]:
            if self.wrench_gui["RFT"] or self.wrench_gui["SS"] or self.wrench_gui["feedback"]:
                self.wrench_fb_live_stream = self.init_live_stream(num_columns=1)
            if self.wrench_gui["ESP"]:
                self.force_esp_live_stream = self.init_live_stream(num_columns=3)
            
        # import debugpy
        # debugpy.listen(("localhost", 5678))
        # print("Waiting for debugger…")
        # debugpy.wait_for_client()
        """
        Initilization
        """
        self.init_sensors()
        self.init_shortcuts()

        self.requested_sensor_num = self.init_args["init_flags"]["vive"] + self.init_args["init_flags"]["esp"] + self.init_args["init_flags"]["ss"] + self.init_args["init_flags"]["rft"] + self.init_args["init_flags"]["log"]

        if self.init_args["init_flags"]["ss"]  == 1:
            if len(self.init_args["SS"]["sides"])>1:
                self.requested_sensor_num += 1
        if self.init_args["init_flags"]["esp"]  == 1:
            if len(self.init_args["ESP"]["sides"])>1:
                self.requested_sensor_num += 1

    """
    Init Sensor Worker / Thread / GUI Helper Functions
    """
    def add_opened_threads(self):
        self.num_opened_threads += 1
        print(f"Threads Opened:{self.num_opened_threads}")        
        
        if self.num_opened_threads == self.requested_sensor_num:
            print("All Threads Opened")
            if self.init_args["init_flags"]["log"] == 1:
                QMetaObject.invokeMethod(self.logger_worker, "sensors_ready", Qt.ConnectionType.QueuedConnection)
    def init_hands(self):
        sides = self.init_args["SS"]["sides"]
        ports = self.init_args["SS"]["ports"]
        self.hands = {}
        for side,port in zip(sides,ports):
            hand = {} 
            # init glove response label
            hand["response_label"] = self.init_response_label(size=[500,190])
            # init glove thread and worker
            hand_thread = QThread()
            hand_worker = SSHandClient('127.0.0.1',port=port,side=side,performer_Id=self.init_args["glove_performer"])
            hand["sensor"] = {"thread":hand_thread,
                              "worker":hand_worker}
            # init fingers and palm plot
            if self.gui_3d_on:
                skeleton = {}
                for i in ["thumb","index","middle","ring","pinky","palm1","palm2","palm3","palm4"]:
                    # init distal position
                    distal = self.init_point(pos=np.array([[0.5,0.5,0.5]]),col=(1,0,0,1))
                    # init distal frame
                    ss_axes = self.init_frame(pos=np.array([[0,0,0]]),rot=self.inert_frame * 0.1 )
                    # init force vecs
                    force_vec = self.init_line(points=np.vstack([np.array([[0,0,0]]), np.array([[1,1,1]])]),color="orange")
                    # init bones
                    if i in ["thumb","index","middle","ring","pinky"]:
                        bones = self.init_line(points=np.vstack([np.array([[0,0,0]]), np.array([[0.1,0.1,0.1]])]),color="purple")
                    else:
                        bones = 0
                    skeleton[i] = {"pos":distal,"rot":ss_axes,"bones":bones,"force_vec":force_vec}
                hand["fingers"] = skeleton
            # init glove live stream plots
            if self.wrench_gui["on?"] and self.wrench_gui["SS"]:
                hand["live_stream_plot"] = self.add_live_stream_plot(live_stream=self.wrench_fb_live_stream,sensor_name= f"SS_{side}",unit="N",dim=3)
            self.hands[f"{side}"] = hand
    def init_vive(self):
        # init response label
        self.vive_label = self.init_response_label(size=[300,80])
        # init vive thread and worker
        self.vive_thread = QThread()
        self.vive_worker = OpenVRServer(performer_ID=self.init_args["glove_performer"])
        # init vive plots
        if self.gui_3d_on:
            self.marker_list = []
            for i in range(self.init_args["VIVE"]):
                # init vive position plot
                vive_point = self.init_point(pos=self.inert_point+i+1,col=(1,0,0,1))
                # init vive frames
                vive_frame = self.init_frame(pos=self.inert_point+i+1,rot=self.inert_frame)
                self.marker_list.append({"pos":vive_point,"rot":vive_frame})
    def init_esp_sensor(self):
        sides = self.init_args["ESP"]["sides"]
        ports = self.init_args["ESP"]["ports"]
        ips = self.init_args["ESP"]["ips"]
        server_ports = self.init_args["ESP"]["server_ports"]
        self.force_modules = {}

        for side,port,ip,server_port in zip(sides,ports,ips,server_ports):
            force_module = {}
            # init response label
            force_module["response_label"] = self.init_response_label(size=[500,50])
            # init esp thread and worker
            esp_thread = QThread()
            esp_worker = ESPUdp(port=port,side=side,ip=ip,server_port=server_port)
            force_module["sensor"] = {"thread":esp_thread,
                                      "worker":esp_worker}
            # init esp live stream plot
            if self.wrench_gui["on?"] and self.wrench_gui["ESP"]:
                esp_live_stream_plots = []
                for i in range(9):
                    esp_live_stream_plots.append(self.add_live_stream_plot(live_stream=self.force_esp_live_stream,sensor_name= f"ESP",unit="N",dim=1))
                force_module["live_stream_plots"] = esp_live_stream_plots
            self.force_modules[f"{side}"] = force_module
    def init_rft_sensor(self):
        # init response label
        self.rft_label = self.init_response_label(size=[300,50])
        # init rft thread and worker
        self.rft_thread = QThread()
        self.rft_worker = RFTSerial(port=self.init_args["RFT"])
        # init rft plot
        if self.gui_3d_on:
            self.rft_point = self.init_point(pos=self.inert_point,col=(1,0,0,1))
            self.rft_frame = self.init_frame(pos=self.inert_point,rot=self.inert_frame)
            self.rft_force_vec = self.init_line(points=np.vstack([np.array([[0,0,0]]), np.array([[1,1,1]])]),color="orange")
        # init rft live stream plot
        if self.wrench_gui["on?"] and self.wrench_gui["RFT"]:
            self.rft_live_stream_plot = self.add_live_stream_plot(live_stream=self.wrench_fb_live_stream,sensor_name= f"RFT",unit="N",dim=3)
            self.rft_tau_live_stream_plot = self.add_live_stream_plot(live_stream=self.wrench_fb_live_stream,sensor_name= f"RFT_Tau",unit="Nm",dim=3)
    def init_logger(self):
        # init response label
        self.logger_label = self.init_response_label(size=[200,150])
        self.logger_thread = QThread()
        self.logger_worker = FMCEvalLogger(sensor_flags=self.init_args["init_flags"],
                                       exp_id=self.init_args["exp_id"],
                                       subject_name=self.init_args["subject_name"],
                                       exe_id=self.init_args["exe_id"],
                                       wrench_type = self.init_args["wrench_type"])
        # init feedback live stream plot
        if self.wrench_gui["on?"] and self.wrench_gui["feedback"]:
            self.feedback_live_stream_plot = self.add_live_stream_plot(live_stream=self.wrench_fb_live_stream,sensor_name= f"Feedback_{self.wrench_type[0]}",unit=self.wrench_type[1],dim=2,autoscale=False,max_range=self.wrench_type[-1])
    def init_shortcuts(self):
        # to start / stop logging at button press
        if self.init_args["init_flags"]["log"]  == 1:
            # to start logging
            start_log = QShortcut("S", self)
            start_log.activated.connect(self.logger_worker.start_worker)
            # to stop logging and close everything
            stop_log = QShortcut("C", self)
            stop_log.activated.connect(self.logger_worker.reset_logger)
            
        close = QShortcut("Q", self)
        close.activated.connect(self.gui_timer.stop)
        close.activated.connect(self.close_workers)
    def init_sensors(self):
        """
        Init sensor thread and worker
        """
        if self.init_args["init_flags"]["log"] == 1:
            self.init_logger()
            self.logger_response = {
            "print_text":"Sensors Not Ready\n",
            "logger_fps":0,
            "instruction": "Wait for Sensors",
            "wrench_instructed": np.array([0])
            }
        if self.init_args["init_flags"]["vive"] == 1:
            self.init_vive()
        if self.init_args["init_flags"]["esp"] == 1:
            self.init_esp_sensor()
        if self.init_args["init_flags"]["ss"] == 1:
            self.init_hands()
        if self.init_args["init_flags"]["rft"] == 1:
            self.init_rft_sensor()

        """
        Move sensor worker to thread 
        Connect intersensor signals
        Connect signals to sensor GUI callbacks
        Connect thread start to start sensor worker, update number of open threads
        Connect worker stop to stop thread at closeup
        Connect thread finished to close app
        """
        if self.init_args["init_flags"]["vive"]  == 1:
            # move worker to thread
            self.vive_worker.moveToThread(self.vive_thread)
            # connect to sensor gui
            self.vive_worker.markers_ready.connect(self.update_vive,type=Qt.ConnectionType.QueuedConnection)   
            # connect thread start to start worker
            self.vive_thread.started.connect(self.vive_worker.start_worker)
            self.vive_thread.started.connect(self.add_opened_threads)
            # connect worker stop to stop thread at closeup
            self.vive_worker.stopped.connect(self.vive_thread.exit)
            # connect thread finished to close app
            self.vive_thread.finished.connect(self.close_app)
        if self.init_args["init_flags"]["esp"]  == 1:
            sides = self.init_args["ESP"]["sides"]
            for side in sides:
                # move worker to thread
                self.force_modules[side]["sensor"]["worker"].moveToThread(self.force_modules[side]["sensor"]["thread"])
                # connect to sensor gui
                if side == "left":
                    self.force_modules[side]["sensor"]["worker"].forces_ready.connect(self.update_left_esp_force,type=Qt.ConnectionType.QueuedConnection)
                else:
                    self.force_modules[side]["sensor"]["worker"].forces_ready.connect(self.update_right_esp_force,type=Qt.ConnectionType.QueuedConnection)
                # connect thread start to start worker
                self.force_modules[side]["sensor"]["thread"].started.connect(self.force_modules[side]["sensor"]["worker"].start_worker)
                self.force_modules[side]["sensor"]["thread"].started.connect(self.add_opened_threads)
                # connect worker stop to stop thread at closeup
                self.force_modules[side]["sensor"]["worker"].stopped.connect(self.force_modules[side]["sensor"]["thread"].exit)
                # connect thread finished to close app
                self.force_modules[side]["sensor"]["thread"].finished.connect(self.close_app)
        if self.init_args["init_flags"]["ss"]  == 1:
            sides = self.init_args["SS"]["sides"]
            for side in sides:
                # move worker to thread
                self.hands[side]["sensor"]["worker"].moveToThread(self.hands[side]["sensor"]["thread"])
                # connect vive to hand
                if self.init_args["init_flags"]["vive"]  == 1:
                    self.vive_worker.markers_ready.connect(self.hands[side]["sensor"]["worker"].update_wrist,type=Qt.ConnectionType.QueuedConnection)
                # connect esp to hand
                if self.init_args["init_flags"]["esp"]  == 1 :
                    self.force_modules[side]["sensor"]["worker"].forces_ready.connect(self.hands[side]["sensor"]["worker"].update_force,type=Qt.ConnectionType.QueuedConnection)
                # connect to sensor gui
                if side == "left":
                    self.hands[side]["sensor"]["worker"].hand_ready.connect(self.update_left_hand,type=Qt.ConnectionType.QueuedConnection)
                else:
                    self.hands[side]["sensor"]["worker"].hand_ready.connect(self.update_right_hand,type=Qt.ConnectionType.QueuedConnection)  
                # connect thread start  to start worker
                self.hands[side]["sensor"]["thread"].started.connect(self.hands[side]["sensor"]["worker"].start_worker)
                self.hands[side]["sensor"]["thread"].started.connect(self.add_opened_threads)
                # connect worker stop to stop thread at closeup
                self.hands[side]["sensor"]["worker"].stopped.connect(self.hands[side]["sensor"]["thread"].exit)
                # connect thread finished to close app
                self.hands[side]["sensor"]["thread"].finished.connect(self.close_app)
        if self.init_args["init_flags"]["rft"]  == 1:
            # move worker to thread
            self.rft_worker.moveToThread(self.rft_thread)
            # connect vive to rft
            if self.init_args["init_flags"]["vive"]  == 1:
                self.vive_worker.markers_ready.connect(self.rft_worker.update_pose,type=Qt.ConnectionType.QueuedConnection)
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
            # connect vive to logger
            if self.init_args["init_flags"]["vive"]  == 1:
                self.vive_worker.markers_ready.connect(self.logger_worker.update_vive,type=Qt.ConnectionType.QueuedConnection)
            # connect hand to logger
            if self.init_args["init_flags"]["ss"]  == 1:
                sides = self.init_args["SS"]["sides"]
                for side in sides:
                    # connect to logger hand
                    if side == "left":
                        self.hands[side]["sensor"]["worker"].hand_ready.connect(self.logger_worker.update_left_hand,type=Qt.ConnectionType.QueuedConnection)
                    else:
                        self.hands[side]["sensor"]["worker"].hand_ready.connect(self.logger_worker.update_right_hand,type=Qt.ConnectionType.QueuedConnection)  
            # connect rft to logger
            if self.init_args["init_flags"]["rft"]  == 1:
                self.rft_worker.forces_ready.connect(self.logger_worker.update_rft,type=Qt.ConnectionType.QueuedConnection)
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
        if self.init_args["init_flags"]["vive"]  == 1:
            self.vive_thread.start()
            self.vive_thread.setPriority(QThread.Priority.TimeCriticalPriority)
        if self.init_args["init_flags"]["esp"]  == 1:
            sides = self.init_args["ESP"]["sides"]
            for side in sides:
                self.force_modules[side]["sensor"]["thread"].start()
                self.force_modules[side]["sensor"]["thread"].setPriority(QThread.Priority.TimeCriticalPriority)
        if self.init_args["init_flags"]["ss"]  == 1:
            sides = self.init_args["SS"]["sides"]
            for side in sides:
                self.hands[side]["sensor"]["thread"].start()
                self.hands[side]["sensor"]["thread"].setPriority(QThread.Priority.TimeCriticalPriority)
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
    def update_vive(self,vive_response):
        self.vive_response = vive_response
    @Slot(dict)
    def update_left_hand(self,left_hand_response):
        self.left_hand_response = left_hand_response
    @Slot(dict)
    def update_right_hand(self,right_hand_response):
        self.right_hand_response = right_hand_response
    @Slot(dict)
    def update_left_esp_force(self,left_esp_response):
        self.left_esp_response = left_esp_response
    @Slot(dict)
    def update_right_esp_force(self,right_esp_response):
        self.right_esp_response = right_esp_response
    @Slot(dict)
    def update_rft(self,rft_response):
        self.rft_response = rft_response
    @Slot(dict)
    def update_logger(self,logger_response):
        self.logger_response = logger_response

    """
    Update Main GUI Helper Functions and Callback
    """
    def update_hand_gui(self,side,hand_response):
        hand = self.hands[side]
        fingers_data = hand_response["fingers_dict"]
        fingers_names = fingers_data["names"]
        fingers_pos = fingers_data["global_t_vecs"]
        fingers_quat = fingers_data["global_quat_vecs"]
        fingers_force_vecs = fingers_data["force_vecs"]

        for distal_name,distal_id,force_vec in zip(["thumb","index","middle","ring","pinky","palm1","palm2","palm3","palm4"],[20,21,22,23,24,25,26,27,28],fingers_force_vecs): 

            pos = fingers_pos[distal_id]
            rot =  R.from_quat(fingers_quat[distal_id]).as_matrix()*0.01
            
            # update distal plot
            self.update_point(plt=hand["fingers"][distal_name]['pos'],pos=pos)
            self.update_frame(plt=hand["fingers"][distal_name]['rot'],pos=pos,rot=rot)

            # update bones for current distal
            if distal_name in ["thumb","index","middle","ring","pinky"]:
                finger_bones_indices = [0]+[i for i, name in enumerate(fingers_names) if distal_name in name]
                bone_pos = fingers_pos[finger_bones_indices]
                bone_pts = np.stack(bone_pos)
                self.update_line(plt=hand["fingers"][distal_name]['bones'],points=bone_pts)

            # update force vec
            pts = np.vstack([pos,pos+force_vec*0.01])
            self.update_line(plt=hand["fingers"][distal_name]['force_vec'],points=pts)
    def update_gui(self):
        super().update_gui()
        if self.wrench_gui["on?"]:
            # update live stream
            if self.wrench_gui["RFT"] or self.wrench_gui["SS"] or self.wrench_gui["feedback"]:
                self.update_live_stream_buffer(live_stream=self.wrench_fb_live_stream)
            if self.wrench_gui["ESP"]:
                self.update_live_stream_buffer(live_stream=self.force_esp_live_stream)
        if hasattr(self, 'vive_response'):
            # update vive info
            fps = self.vive_response["vive_fps"]
            print_text = self.vive_response["print_text"]
            self.update_response_label(self.vive_label,f'FPS:{fps}\n{print_text}')

            if self.gui_3d_on:
                # update gui
                markers_pos = self.vive_response["trackers_pos"]
                markers_frame = self.vive_response["trackers_frame"]
                for i,marker in enumerate(self.marker_list):
                    cur_marker_pos = markers_pos[i]
                    cur_marker_frame =  R.from_quat(markers_frame[i]).as_matrix()*0.1

                    self.update_point(plt=marker["pos"],pos=cur_marker_pos)
                    self.update_frame(plt=marker["rot"],pos=cur_marker_pos,rot=cur_marker_frame) 
        if hasattr(self, 'left_hand_response'):
            # update hand info
            print_text = self.left_hand_response["print_text"]
            hand = self.hands["left"]
            fps = self.left_hand_response["hand_fps"]
            self.update_response_label(hand["response_label"],f'FPS:{fps}\n{print_text}')

            if self.gui_3d_on:
                # update gui
                self.update_hand_gui("left",self.left_hand_response)
            if self.wrench_gui["on?"] and self.wrench_gui["SS"]:
                # update live stream plot
                self.update_live_stream_plot(self.wrench_fb_live_stream,hand["live_stream_plot"],np.sum(self.left_hand_response["fingers_dict"]["force_vecs"],axis=0),dim=3)
        if hasattr(self, 'right_hand_response'):
            # update hand info
            print_text = self.right_hand_response["print_text"]
            hand = self.hands["right"]
            fps = self.right_hand_response["hand_fps"]
            self.update_response_label(hand["response_label"],f'FPS:{fps}\n{print_text}')

            if self.gui_3d_on:
                # update gui
                self.update_hand_gui("right",self.right_hand_response)
            if self.wrench_gui["on?"] and self.wrench_gui["SS"]:
                # update live stream plot
                self.update_live_stream_plot(self.wrench_fb_live_stream,hand["live_stream_plot"],np.sum(self.right_hand_response["fingers_dict"]["force_vecs"],axis=0),dim=3)
        if hasattr(self, 'left_esp_response'):
            # update esp info
            force_module = self.force_modules["left"]      
            force_data = self.left_esp_response["force_data"]
            fps = self.left_esp_response["esp_fps"]
            self.update_response_label(force_module["response_label"],f'FPS:{fps}\n{force_data}')
            if self.wrench_gui["on?"] and self.wrench_gui["ESP"]:
                # update live stream plot
                for i,live_stream_plot in enumerate(force_module["live_stream_plots"]):
                    self.update_live_stream_plot(self.force_esp_live_stream,live_stream_plot,np.array([force_data[i]]),dim=1)
        if hasattr(self, 'right_esp_response'):
            # update esp info
            force_module = self.force_modules["right"]      
            force_data = self.right_esp_response["force_data"]
            fps = self.right_esp_response["esp_fps"]
            self.update_response_label(force_module["response_label"],f'FPS:{fps}\n{force_data}')
            if self.wrench_gui["on?"] and self.wrench_gui["ESP"]:
                # update live stream plot
                for i,live_stream_plot in enumerate(force_module["live_stream_plots"]):
                    self.update_live_stream_plot(self.force_esp_live_stream,live_stream_plot,np.array([force_data[i]]),dim=1)
        if hasattr(self, 'rft_response'):
            # update rft info
            force_data = self.rft_response["rft_data_arr"]
            fps = self.rft_response["rft_fps"]
            self.update_response_label(self.rft_label,f"FPS:{fps}\n{force_data}")
            
            if self.gui_3d_on:
                # update gui
                rft_pos = self.rft_response["rft_pose"].t
                rft_frame = self.rft_response["rft_pose"].R*0.5
                force_vec = self.rft_response["rft_data_arr"]
                self.update_point(plt=self.rft_point,pos=rft_pos)
                self.update_frame(plt=self.rft_frame,pos=rft_pos,rot=rft_frame) 
                self.update_line(plt=self.rft_force_vec,points=np.vstack([rft_pos,rft_pos+force_vec[:3]*0.01]))

            if self.wrench_gui["on?"] and self.wrench_gui["RFT"]:
                self.update_live_stream_plot(self.wrench_fb_live_stream,self.rft_live_stream_plot,force_data,dim=3)
                self.update_live_stream_plot(self.wrench_fb_live_stream,self.rft_tau_live_stream_plot,force_data[3:],dim=3)
        if hasattr(self, 'logger_response'):
            print_text = self.logger_response["print_text"]
            instruction = self.logger_response["instruction"]
            wrench_instructed = self.logger_response["wrench_instructed"]
            fps = self.logger_response["logger_fps"]
            self.update_response_label(self.logger_label,f"{print_text}FPS:{fps}\n{instruction}")

            if self.wrench_gui["on?"] and self.wrench_gui["feedback"]:
                self.update_live_stream_plot(self.wrench_fb_live_stream,self.feedback_live_stream_plot,wrench_instructed,dim=2)
    
    """
    Cleanup
    """
    def close_worker_thread(self,worker):
        QMetaObject.invokeMethod(worker, "stop", Qt.ConnectionType.QueuedConnection)
    def close_workers(self):
        if hasattr(self, 'vive_response'):
            self.close_worker_thread(self.vive_worker)
        if hasattr(self, 'rft_response'):
            self.close_worker_thread(self.rft_worker)
        if hasattr(self, 'left_hand_response'):
            self.close_worker_thread(self.hands["left"]["sensor"]["worker"])
        if hasattr(self, 'right_hand_response'):
            self.close_worker_thread(self.hands["right"]["sensor"]["worker"])
        if hasattr(self, 'left_esp_response'):
            self.close_worker_thread(self.force_modules["left"]["sensor"]["worker"])
        if hasattr(self, 'right_esp_response'):
            self.close_worker_thread(self.force_modules["right"]["sensor"]["worker"])
        if hasattr(self, 'logger_response'):
            # import time
            # time.sleep(5)
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
4
if __name__ == "__main__":
    try:
        argv = sys.argv[1]
    except:
        argv ={"gui_freq":60,
                "exp_id":"exp1",
                "subject_name":"JQ",
                "glove_performer":"JQ",
                "exe_id":"exe1",
                "init_flags":{"vive":1,
                                "esp":1,
                                "ss":1,
                                "rft":1,
                                "log":1,
                                "gui_3d_on":True,
                                "wrench_gui":{"on?":True,"RFT":False,"ESP":False,"SS":False,"feedback":True}},
                "wrench_type":["force","N",15,20],
                "VIVE":2,
                "RFT":"COM4",
                # "ESP":{"sides":["left","right"],"ports":[4211,4212],"ips":["192.168.240.121","192.168.240.27"],"server_ports":[4213,4214]},
                # "SS":{"sides":["left","right"],"ports": [9004,9003]}}

                "ESP":{"sides":["right"],"ports":[4212],"ips":["192.168.240.27"],"server_ports":[4214]},
                "SS":{"sides":["right"],"ports": [9003]}}
        
                # "ESP":{"sides":["left"],"ports":[4211],"ips":["192.168.240.121"],"server_ports":[4213]},        
                # "SS":{"sides":["left"],"ports": [9004]}}
                
        argv = json.dumps(argv)
    init_args = json.loads(argv)
    app = QtWidgets.QApplication(sys.argv)
    w = FMCGloveEval(init_args)
    w.setWindowTitle("ForceMoCap")
    w.show()

    import psutil
    p = psutil.Process(os.getpid())
    p.nice(psutil.REALTIME_PRIORITY_CLASS)  # or REALTIME_PRIORITY_CLASS
    sys.exit(app.exec())
        