import sys,os
sys.path.append(os.path.join(os.path.dirname(__file__)))
from vive_helper.openvr_platform_tool import *

from PySide6.QtCore import QObject, QThread, Signal,QTimer,Slot,QElapsedTimer,Qt,QMetaObject
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget
import debugpy

class OpenVRServer(QObject):
    markers_ready = Signal(dict)
    stopped = Signal()
    def __init__(self,performer_ID = "JQ"):
        super().__init__()
        self.ground_tracker_rotation = SO3().Rz(180, 'deg').R @ SO3().Rx(90, 'deg').R 
        
        json_path = os.path.join(f"{os.path.dirname(__file__)}/../../experiments/exp1/hand_measurements/{performer_ID}", "wrist.json")
        with open(json_path, 'r') as f:
                data = json.load(f)
        self.right_wrist_offset = np.array(data['right_wrist_offset'])  
        self.left_wrist_offset = np.array(data['left_wrist_offset'])

        # FPS Calculator
        self.vive_frame_count = 0
        self.vive_fps = 0
        self.vive_timer = QElapsedTimer() # use the system clock
        self.vive_timer.start()
        self.vive_cur_time = self.vive_timer.elapsed()
        self.vive_last_time = self.vive_timer.elapsed()

        print("Vive Started")

    """
    OpenVR Callback
    """
    def read_vive_data(self):
        # debugpy.debug_this_thread()

        trackers_pos = []
        trackers_frame = []
        trackers_name = []
        wrists_pos = {}
        wrists_frame = {}
        try:
            # update vive frame rate
            self.vive_frame_count += 1
            self.vive_cur_time = self.vive_timer.elapsed()
            if self.vive_cur_time-self.vive_last_time >= 1000:
                self.vive_fps = self.vive_frame_count * 1000 / (self.vive_cur_time-self.vive_last_time)
                self.vive_last_time = self.vive_cur_time
                self.vive_frame_count = 0

            print_text = ""
            for i,tracker in enumerate(self.trackers):
                assert isinstance(tracker, vr_tracked_device)
                pos_inert,euler,quat,t_mat,valid =  tracker.get_all_pose() # return the pose in euler (ZYX) and transformation matrix
                pos_inert = np.array(pos_inert)
                R_inert = R.from_quat(quat)
                if i == 0:
                    R_inert = R.from_matrix(np.matmul(R_inert.as_matrix(),self.ground_tracker_rotation)) # rotate the ground tracker frame for convenience
                quat_inert = R_inert.as_quat()
                name = tracker.get_serial()

                # transform everything to known ground point (first tracker)
                if i == 0: # first tracker is the new inert
                    ground_T = SE3.Rt(R_inert.as_matrix(),pos_inert)
                    ground_point = ground_T.inv()@ground_T
                    pos_inert = ground_point.t
                    R_inert = R.from_matrix(ground_point.R) # correct the orientation to inertial frame
                    quat_inert = R_inert.as_quat()
                else:
                    inert_T = SE3.Rt(R_inert.as_matrix(),pos_inert)
                    cur_point = ground_T.inv()@inert_T
                    pos_inert = cur_point.t+np.array([0,0,(26-3.3)/100]) # 0.267 - mdf to top, 0.048 mdf to rft
                    # 26/100 , 3.3/100
                    R_inert = R.from_matrix(cur_point.R) # correct the orientation to inertial frame
                    quat_inert = R_inert.as_quat()

                print_text += f"Marker {name}: {pos_inert*100}\n"

                if name == "LHR-C700522C" or name == "LHR-26922E89":
                    if name == "LHR-C700522C":
                        wrist_offset = self.left_wrist_offset 
                    elif name == "LHR-26922E89":
                        wrist_offset = self.right_wrist_offset

                    wrist_pos = pos_inert+R_inert.as_matrix()@wrist_offset
                    wrists_pos[name] = wrist_pos
                    wrists_frame[name] = quat_inert

                if valid:
                    trackers_pos.append(pos_inert)
                    trackers_frame.append(quat_inert)
                    trackers_name.append(name)
                else:
                    trackers_pos.append(np.array([0,0,0]))
                    trackers_frame.append(np.array([0,0,0,1]))
                    trackers_name.append("null")


            self.data = {
                "trackers_pos":trackers_pos,
                "trackers_frame":trackers_frame,
                "trackers_name":trackers_name,
                "wrists_pos":wrists_pos,
                "wrists_frame":wrists_frame,
                "print_text":print_text,
                "vive_fps":self.vive_fps
            }
            self.markers_ready.emit(self.data)
        except Exception as e:
            self.markers_ready.emit(self.data)
            pass

    """
    Initialization Callback
    """
    def start_worker(self):
        self.vr_plat = triad_openvr()
        self.trackers = self.vr_plat.get_trackers() 

        self.poll_timer = QTimer()
        self.poll_timer.setTimerType(Qt.PreciseTimer)
        self.poll_timer.timeout.connect(self.read_vive_data)
        self.poll_timer.start(int(1/90*1000))

    """
    External Signal Callbacks
    """
    @Slot()
    def stop(self):
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
        self.worker = OpenVRServer()
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.start_worker)
        self.worker.markers_ready.connect(self.update_label)
        self.button.clicked.connect(self.cleanup)

        self.thread.start()

    def update_label(self, text):
        self.label.setText(f'info: {text["print_text"]}{text["vive_fps"]}')

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