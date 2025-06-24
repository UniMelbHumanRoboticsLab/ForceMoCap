import sys,os
sys.path.append(os.path.join(os.path.dirname(__file__)))
from openvr_platform_tool import *
import threading

class OpenVRServer:
    def __init__(self):

        self.vr_plat = triad_openvr()
        self.trackers = self.vr_plat.get_trackers() 
        self.trackers_pos = [0 for i in self.trackers] # position
        self.trackers_frame = [0 for i in self.trackers] # orientation
        self.trackers_vel = [0 for i in self.trackers]

        self.__thread = threading.Thread(target=self.__readResponseRunner)
        self.__thread.daemon = True
        self._lock = threading.Lock()
        self.__thread.start()

    def __readResponseRunner(self):
        while True:
            cur_trackers_pos = []
            cur_trackers_frame = []
            cur_trackers_vel = []
            try:
                for tracker in self.trackers:
                    assert isinstance(tracker, vr_tracked_device)
                    position,euler,quat,t_mat,valid =  tracker.get_all_pose() # return the pose in euler (ZYX) and transformation matrix
                    # pose,valid = tracker.get_pose_quaternion()
                    # position = pose[:3]
                    # quat = pose[3:]
                    
                    if valid:
                        vel = tracker.get_velocity()._getArray()[0:]
                        cur_trackers_pos.append(position)
                        cur_trackers_frame.append(quat)
                        cur_trackers_vel.append(vel)
                    else:
                        cur_trackers_pos.append(np.array([0,0,0]))
                        cur_trackers_frame.append(np.array([0,0,0,0]))
                        cur_trackers_vel.append([0,0,0])

                self.trackers_pos = cur_trackers_pos
                self.trackers_frame = cur_trackers_frame
                self.trackers_vel = cur_trackers_vel

            except Exception as e:
                # print(e)
                pass
    
    def get_trackers_pose(self):
        with self._lock:
            return self.trackers_pos,self.trackers_frame
    
    def get_trackers_vel(self):
        with self._lock:
            return self.trackers_vel

if __name__ == "__main__":
    vive = OpenVRServer()
    while True:
        print(vive.get_trackers_pose())
        pass