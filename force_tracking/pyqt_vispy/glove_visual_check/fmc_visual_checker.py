import os
import numpy as np
np.set_printoptions(
    precision=4,
    linewidth=np.inf,   
    formatter={'float_kind': lambda x: f"{x:.4f}"}
)
import pandas as pd
from spatialmath import SE3
from PySide6.QtCore import QObject, Signal,QTimer,Slot,QElapsedTimer,Qt
import debugpy

def read_hand_csv(path,side):
    hand = pd.read_csv(f"{path}/{side}_hand.csv").to_numpy()[:,2:]
    hand_col_head = pd.read_csv(f"{path}/{side}_hand.csv").columns.to_numpy()[2:]
    hand_indices = {}
    for spots in ["thumb","index","middle","ring","pinky","palm_0","palm_1","palm_2","palm_3"]:
        finger_indices = [i for i, s in enumerate(hand_col_head) if spots.lower() in s.lower()]
        hand_indices[spots] = finger_indices
    return hand, hand_col_head, hand_indices
class FMCVisualChecker(QObject):
    time_ready = Signal(dict)
    finish_save = Signal()
    stopped = Signal()
    def __init__(self,sensor_flags,sides,exp_id,subject_name,exe_id,wrench_type):

        super().__init__()
        self.sensor_flags = sensor_flags
        self.sides = sides
        self.wrench_type = wrench_type
        self.data_path = f"./experiments/{exp_id}/data/{subject_name}/{exe_id}/{wrench_type[0]}_{wrench_type[2]}"

        # read logged data
        if self.sensor_flags["ss"] == 1:
            if "left" in self.sides:
                self.left_hand_data, self.left_hand_col,self.left_hand_indices = read_hand_csv(f"{self.data_path}/", "left")
            else:
                self.left_hand_data = 0
                
            if "right" in self.sides:
                self.right_hand_data, self.right_hand_col,self.right_hand_indices = read_hand_csv(f"{self.data_path}/", "right")
            else:
                self.right_hand_data = 0

        if self.sensor_flags["rft"] == 1:
            self.rft = pd.read_csv(f"{self.data_path}/rft_wrenches.csv").to_numpy()
        else:
            self.rft = 0

        self.frame_id = 0
        self.total_frames = len(self.rft) if self.sensor_flags["rft"]==1 else 1000

        # FPS Calculator
        self.logger_frame_count = 0
        self.logger_fps = 0
        self.logger_timer = QElapsedTimer() # use the system clock
        self.logger_timer.start()
        self.logger_cur_time = self.logger_timer.elapsed()
        self.logger_last_time = self.logger_timer.elapsed()
        self.elapsed_time = 0

        print("FMC Visual Checker Started")
    
    """
    Logging Callback
    """
    def reprocess_hand_data(self,hand_data,hand_indices):
        # process hand data
        global_t_arr = []
        global_quat_arr = []
        force_vecs = []
        for spots in ["thumb","index","middle","ring","pinky","palm_0","palm_1","palm_2","palm_3"]:
            # print(f"{spots}: {self.left_hand_col[self.left_hand_indices[spots]]}")
            data = hand_data[hand_indices[spots]]
            global_t_arr.append(data[:3])
            global_quat_arr.append(data[3:7])
            force_vecs.append(data[7:])
        hand_data_processed = {
            "global_t_arr": global_t_arr,
            "global_quat_arr": global_quat_arr,
            "force_vecs": force_vecs
        }
        return hand_data_processed
        
    def display_current_data(self):
        self.frame_id += 1
        if self.frame_id >= self.total_frames:
            self.frame_id = 0
            self.logger_start_time = self.logger_timer.elapsed()
            
        # update FPS
        print_text = f"Logging\n"
        self.logger_frame_count += 1
        self.logger_cur_time = self.logger_timer.elapsed()
        self.elapsed_time = (self.logger_cur_time-self.logger_start_time)/1000
        print_text += f"Time Elapsed:{self.elapsed_time}\n"
        if self.logger_cur_time-self.logger_last_time >= 1000:
            self.logger_fps = self.logger_frame_count * 1000 / (self.logger_cur_time-self.logger_last_time)
            self.logger_last_time = self.logger_cur_time
            self.logger_frame_count = 0

        # process hands
        if self.sensor_flags["ss"] == 1:
            if "left" in self.sides:
                self.left_hand_processed = self.reprocess_hand_data(self.left_hand_data[self.frame_id],self.left_hand_indices)
            else:
                self.left_hand_processed = 0

            if "right" in self.sides:
                self.right_hand_processed = self.reprocess_hand_data(self.right_hand_data[self.frame_id],self.right_hand_indices)
            else:
                self.right_hand_processed = 0

        # process rft
        if self.sensor_flags["rft"] == 1:
            rft_data = {
                "rft_data_arr":self.rft[self.frame_id,3:],
                "rft_pose":SE3()}
            measured_wrench = np.array([np.linalg.norm(rft_data["rft_data_arr"][:3])]) if self.wrench_type=="force" else np.array([np.linalg.norm(rft_data["rft_data_arr"][:3])])
        else:
            rft_data = 0
            measured_wrench = np.array([0])

        # emit the signal
        data = {
            "print_text":print_text,
            "logger_fps":self.logger_fps,
            "frame_id": self.frame_id,
            "left_hand_response": self.left_hand_processed,
            "right_hand_response": self.right_hand_processed,
            "rft_response": rft_data,
            "measured_wrench": measured_wrench,
        }
        self.time_ready.emit(data)
    
    """
    Initialization Callback
    """
    @Slot()
    def start_worker(self):
        self.poll_timer = QTimer()
        self.poll_timer.setTimerType(Qt.PreciseTimer)
        self.poll_timer.timeout.connect(self.display_current_data)
        self.poll_timer.start(int(1/150*1000))
        self.logger_start_time = self.logger_timer.elapsed()
        
    """
    External Signals Callbacks
    """
    @Slot()
    def stop(self):
        if hasattr(self, 'poll_timer'):
            self.poll_timer.stop()
        self.stopped.emit()
    @Slot()
    def stop_vc(self):
        # debugpy.debug_this_thread()
        if hasattr(self, 'poll_timer'):
            self.poll_timer.stop()
        
        # emit the signal
        self.time_ready.emit({
            "print_text":"Finish Visual Check\n",
            "logger_fps": 0.0,
            "frame_id": self.frame_id,
            "left_hand_response": 0,
            "right_hand_response": 0,
            "rft_response": 0
        })
        self.finish_save.emit()
        
    """
    Helper Function
    """    
    def save_file(self,path,df:pd.DataFrame,item):
        if not os.path.isdir(path):
            os.makedirs(path)
        df.to_csv(f"{path}/{item}.csv")    

    
