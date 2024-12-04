import pyrealsense2 as rs
import numpy as np
from datetime import datetime


class RealsenseCamera:

    def __init__(self, recording):
        # Configure depth and color streams
        print("Loading Intel Realsense Camera")
        self.pipeline = rs.pipeline()

        config = rs.config()
        fps = 30
        self.recording = recording
        if(config.can_resolve(self.pipeline)):
                if(recording):
                        config.enable_record_to_file(datetime.now().strftime("../%d_%m_%Y-%H_%M_%S")+'.bag')#Save to file as well
                print("Realsense Camera Ok")
                config.enable_stream(rs.stream.color, 1280, 720, rs.format.rgb8, fps)
                config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, fps)
                self.hole_filling = rs.hole_filling_filter() # hole filling filter to prevent zero depth
                # Start streaming
                p_profile = self.pipeline.start(config)
                align_to = rs.stream.color
                self.align = rs.align(align_to)
                if(recording):
                        self.recorder = p_profile.get_device().as_recorder()
                        self.recorder.pause()
                self.init=True
        else:
                self.init=False
                print("Realsense Camera Error")

    def is_init(self):
        return self.init;

    def get_frames(self):
        return self.pipeline.wait_for_frames()

    def get_frame_stream(self):
        frames = self.pipeline.wait_for_frames()
        aligned_frames = self.align.process(frames)
        # get depth and fill holes from depth
        depth_frame = aligned_frames.get_depth_frame()
        depth_frame = self.hole_filling.process(depth_frame)            
        color_frame = aligned_frames.get_color_frame()
        
        if not depth_frame or not color_frame:
            # If there is no frame, probably camera not connected, return False
            print("Error, impossible to get the frame, make sure that the Intel Realsense camera is correctly connected")
            return False, None, None
        
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        depth_profile = rs.video_stream_profile(self.pipeline.get_active_profile().get_stream(rs.stream.depth))
        self.depth_intrinsics = depth_profile.get_intrinsics()
        return True, color_image, depth_image


    def imgTo3D(self, imgPos, depth_image):
        pos3D={};
        depthRS = []
        pos3DMat = []
        for id,pos in imgPos.items():
            if(not np.isnan(pos[0]) and not np.isnan(pos[1])):
                    d = depth_image[int(pos[1]), int(pos[0])]
                    p = rs.rs2_deproject_pixel_to_point(self.depth_intrinsics, [pos[0], pos[1]], d)
                    pos3D[id]=[p[0], p[1], p[2],d]
                    pos3DMat.append([p[0], p[1], p[2]])
                    depthRS.append(d)
            else:
                    pos3D[id]=[np.NAN, np.NAN, np.NAN,0]
                    pos3DMat.append([np.NAN, np.NAN, np.NAN,0])
                    depthRS.append(0)
        return pos3D,np.array(depthRS),pos3DMat
        
    
    def release(self):
        self.pipeline.stop()

    def project(self,intr, x, y, depth,):
        return rs.rs2_deproject_pixel_to_point(self,intr, [x,y], depth)


