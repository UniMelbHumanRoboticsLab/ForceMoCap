import os, sys,json
from fmc_visual_checker import FMCVisualChecker
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from base.fmc_base import FMCBase

import numpy as np
from scipy.spatial.transform import Rotation as R

from PySide6 import QtWidgets
from PySide6.QtGui import QShortcut
from PySide6.QtCore import QThread,Qt,QMetaObject,Slot

import debugpy

class FMCGloveVC(FMCBase):
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
        self.init_sensor_display()
        self.init_shortcuts()

    """
    Init Sensor Worker / Thread / GUI Helper Functions
    """
    def add_opened_threads(self):
        self.num_opened_threads += 1
        print(f"Threads Opened:{self.num_opened_threads}")
    def init_hands(self):
        sides = self.init_args["SS"]["sides"]
        self.hands = {}
        for side in sides:
            hand = {} 
            # init fingers and palm plot
            if self.gui_3d_on:
                skeleton = {}
                for i in ["thumb","index","middle","ring","pinky","palm_0","palm_1","palm_2","palm_3"]:
                    # init distal position
                    distal = self.init_point(pos=np.array([[0.5,0.5,0.5]]),col=(1,0,0,1))
                    # init distal frame
                    ss_axes = self.init_frame(pos=np.array([[0,0,0]]),rot=self.inert_frame * 0.1)
                    # init force vecs
                    force_vec = self.init_line(points=np.vstack([np.array([[0,0,0]]), np.array([[1,1,1]])]),color="orange")

                    skeleton[i] = {"pos":distal,"rot":ss_axes,"force_vec":force_vec}
                hand["fingers"] = skeleton
            # init glove live stream plots
            if self.wrench_gui["on?"] and self.wrench_gui["SS"]:
                hand["live_stream_plot"] = self.add_live_stream_plot(live_stream=self.wrench_fb_live_stream,sensor_name= f"SS_{side}",unit="N",dim=3)
            self.hands[f"{side}"] = hand
    def init_rft(self):
        # init rft plot
        if self.gui_3d_on:
            self.rft_point = self.init_point(pos=self.inert_point,col=(1,0,0,1))
            self.rft_frame = self.init_frame(pos=self.inert_point,rot=self.inert_frame)
            self.rft_force_vec = self.init_line(points=np.vstack([np.array([[0,0,0]]), np.array([[1,1,1]])]),color="orange")
        # init rft live stream plot
        if self.wrench_gui["on?"] and self.wrench_gui["RFT"]:
            self.rft_live_stream_plot = self.add_live_stream_plot(live_stream=self.wrench_fb_live_stream,sensor_name= f"RFT",unit="N",dim=3)
            self.rft_tau_live_stream_plot = self.add_live_stream_plot(live_stream=self.wrench_fb_live_stream,sensor_name= f"RFT_Tau",unit="Nm",dim=3)
    def init_visual_checker(self):
        # init response label
        self.logger_label = self.init_response_label(size=[500,150])
        self.vc_thread = QThread()
        self.vc_worker = FMCVisualChecker(sensor_flags=self.init_args["init_flags"],
                                          sides=self.init_args["SS"]["sides"],
                                          exp_id=self.init_args["exp_id"],
                                          subject_name=self.init_args["subject_name"],
                                          exe_id=self.init_args["exe_id"],
                                          wrench_type=self.wrench_type)
        # init feedback live stream plot
        if self.wrench_gui["on?"] and self.wrench_gui["feedback"]:
            self.feedback_live_stream_plot = self.add_live_stream_plot(live_stream=self.wrench_fb_live_stream,sensor_name= f"Feedback_{self.wrench_type[0]}",unit=self.wrench_type[1],dim=1)
    def init_shortcuts(self):
        # to start / stop logging at button press
        if self.init_args["init_flags"]["visual_check"]  == 1:
            # to start logging
            start_log = QShortcut("S", self)
            start_log.activated.connect(self.vc_worker.start_worker)
            # to stop logging and close everything
            stop_log = QShortcut("C", self)
            stop_log.activated.connect(self.vc_worker.stop_vc)
            stop_log.activated.connect(self.gui_timer.stop)
            
        close = QShortcut("Q", self)
        close.activated.connect(self.gui_timer.stop)
        close.activated.connect(self.close_workers)
    def init_sensor_display(self):
        """
        Init sensor displays and workers
        """
        if self.init_args["init_flags"]["ss"] == 1:
            self.init_hands()
        if self.init_args["init_flags"]["rft"] == 1:
            self.init_rft()
        if self.init_args["init_flags"]["visual_check"] == 1:
            self.init_visual_checker()
            self.vc_response = {
            "print_text":"Idle\n",
            "logger_fps":0,
            "frame_id": 0,
            "measured_wrench": [0],
            }
        
        """
        Move sensor worker to thread 
        Connect intersensor signals
        Connect signals to sensor GUI callbacks
        Connect thread start to start sensor worker, update number of open threads
        Connect worker stop to stop thread at closeup
        Connect thread finished to close app
        """
        if self.init_args["init_flags"]["visual_check"]  == 1:
            # move worker to thread
            self.vc_worker.moveToThread(self.vc_thread)
            # connect logger to sensor gui
            self.vc_worker.time_ready.connect(self.update_visual_checker,type=Qt.ConnectionType.QueuedConnection)
            # connect thread start to add opened threads  
            self.vc_thread.started.connect(self.add_opened_threads)
            # connect logger finished saving to close workers
            self.vc_worker.finish_save.connect(self.close_workers)
            # connect worker stop to stop thread at closeup
            self.vc_worker.stopped.connect(self.vc_thread.exit)
            # connect thread finished to close app
            self.vc_thread.finished.connect(self.close_app)

        """
        Start threads
        """
        if self.init_args["init_flags"]["visual_check"]  == 1:
            self.vc_thread.start()
            self.vc_thread.setPriority(QThread.Priority.TimeCriticalPriority)
        
    """
    Update Sensor Variable Callbacks
    """
    @Slot(dict)
    def update_visual_checker(self,vc_response):
        self.vc_response = vc_response
        if self.init_args["init_flags"]["rft"] == 1:
            self.rft_response = vc_response["rft_response"]
        if self.init_args["init_flags"]["ss"] == 1:
            if "left" in self.init_args["SS"]["sides"]:
                self.left_hand_response = vc_response["left_hand_response"]
            if "right" in self.init_args["SS"]["sides"]:
                self.right_hand_response = vc_response["right_hand_response"]

    """
    Update Main GUI Helper Functions and Callback
    """
    def update_hand_gui(self,side,hand_response):
        hand = self.hands[side]
        fingers_pos = hand_response["global_t_vecs"]
        fingers_quat = hand_response["global_quat_vecs"]
        fingers_force_vecs = hand_response["force_vecs"]

        for distal_name,finger_pos,finger_quat,force_vec in zip(["thumb","index","middle","ring","pinky","palm_0","palm_1","palm_2","palm_3"],fingers_pos,fingers_quat,fingers_force_vecs): 
            pos = finger_pos
            rot =  R.from_quat(finger_quat).as_matrix()*0.01
            
            # update distal plot
            self.update_point(plt=hand["fingers"][distal_name]['pos'],pos=pos)
            self.update_frame(plt=hand["fingers"][distal_name]['rot'],pos=pos,rot=rot)

            # update force vec
            pts = np.vstack([pos,pos+force_vec*0.01])
            self.update_line(plt=hand["fingers"][distal_name]['force_vec'],points=pts)
    def update_gui(self):
        super().update_gui()
        if self.wrench_gui["on?"]:
            # update live stream
            if self.wrench_gui["RFT"] or self.wrench_gui["SS"] or self.wrench_gui["feedback"]:
                self.update_live_stream_buffer(live_stream=self.wrench_fb_live_stream)
        if hasattr(self, 'left_hand_response'):
            # update hand info
            hand = self.hands["left"]
            if self.gui_3d_on:
                # update gui
                self.update_hand_gui("left",self.left_hand_response)
            if self.wrench_gui["on?"] and self.wrench_gui["SS"]:
                # update live stream plot
                self.update_live_stream_plot(self.wrench_fb_live_stream,hand["live_stream_plot"],np.sum(self.left_hand_response["force_vecs"],axis=0),dim=3)
        if hasattr(self, 'right_hand_response'):
            # update hand info
            hand = self.hands["right"]
            if self.gui_3d_on:
                # update gui
                self.update_hand_gui("right",self.right_hand_response)
            if self.wrench_gui["on?"] and self.wrench_gui["SS"]:
                # update live stream plot
                self.update_live_stream_plot(self.wrench_fb_live_stream,hand["live_stream_plot"],np.sum(self.right_hand_response["force_vecs"],axis=0),dim=3)
        if hasattr(self, 'rft_response'):
            # update rft info
            force_data = self.rft_response["rft_data_arr"]
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
        if hasattr(self, 'vc_response'):
            print_text = self.vc_response["print_text"]
            fps = self.vc_response["logger_fps"]
            frame_id = self.vc_response["frame_id"]
            measured_wrench = self.vc_response["measured_wrench"]
            self.update_response_label(self.logger_label,f"{print_text}Frame:{frame_id}\n")

            if self.wrench_gui["on?"] and self.wrench_gui["feedback"]:
                self.update_live_stream_plot(self.wrench_fb_live_stream,self.feedback_live_stream_plot,measured_wrench,dim=1)
    
    """
    Cleanup
    """
    def close_worker_thread(self,worker):
        QMetaObject.invokeMethod(worker, "stop", Qt.ConnectionType.QueuedConnection)
    def close_workers(self):
        if hasattr(self, 'vc_response'):
            self.close_worker_thread(self.vc_worker)
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
               "exp_id":"exp1",
               "subject_name":"JQ",
               "glove_performer":"JQ",
               "exe_id":"exe1",
               "init_flags":{"ss":1,
                             "rft":1,
                             "visual_check":1,
                             "gui_3d_on":True,
                             "wrench_gui":{"on?":True,"RFT":True,"SS":False,"feedback":True}},
                "wrench_type":["force","N",15],
                "SS":{"sides":["right"]}}
        
        argv = json.dumps(argv)

    init_args = json.loads(argv)
    app = QtWidgets.QApplication(sys.argv)
    w = FMCGloveVC(init_args)
    w.setWindowTitle("ForceMoCap")
    w.show()

    import psutil
    p = psutil.Process(os.getpid())
    p.nice(psutil.REALTIME_PRIORITY_CLASS)  # or REALTIME_PRIORITY_CLASS
    sys.exit(app.exec())
        