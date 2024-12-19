import numpy as np
import time
from mo_cap.depth_cam.FLNL import * 

from enum import IntEnum
import mediapipe as mp
import cv2
from collections import deque
import matplotlib.pyplot as plt
import keyboard

from PyQt6 import QtWidgets
from PyQt6.QtGui import QPixmap,QImage
from PyQt6.QtWidgets import QWidget,QLabel
from PyQt6.QtCore import QThread,pyqtSignal,Qt 
import pyqtgraph as pg
from pyqtgraph import mkPen
from pglive.kwargs import Axis
from pglive.sources.data_connector import DataConnector
from pglive.sources.live_axis import LiveAxis
from pglive.sources.live_axis_range import LiveAxisRange
from pglive.sources.live_plot import LiveLinePlot
from pglive.sources.live_plot_widget import LivePlotWidget
from pglive.kwargs import LeadingLine
import pandas as pd
from util_files.jq_util import *

"""
Joints points names to IDs:
"""
class J(IntEnum):
    L_Y = 2 #Left eye
    R_Y = 5 #Right eye
    L_H = 23 #Left Hip
    R_H = 24 #Right Hip
    L_S = 11 #Left Shoulder
    R_S = 12 #Right Shoulder
    L_E = 13 #Left Elbow
    R_E = 14 #Right Elbow
    L_W = 15 #Left Wrist
    R_W = 16 #Right Wrist
submovement = 0
"""
Pose Detector to find pose and plot pose in 3D
"""
class PoseDetector:
    def __init__(self):
        self.mpDraw = mp.solutions.drawing_utils
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose(model_complexity=0, #Use lighter model: faster w/ sufficient tracking
                                     min_detection_confidence=0.5,
                                     min_tracking_confidence=0.4,
                                     smooth_landmarks=True #better result given mvt continuity required
                                     )
    
    """
    find joint positions in image coordinates
    jointsImgPos - joint position in image coordinates
    img -
    jointPosMP - 
    np.array(jointsDepthMP) - 
    cantFindPose
    """
    def findPose(self, img, arm_side, objects_to_track, draw=False):
        self.results = self.pose.process(img)
        if draw:
            if arm_side=='r':
                POSE_CONNECTIONS = frozenset([(5, 2), (11, 12), (12, 14), (14, 16), (11, 23), (12, 24),(23,24)])
            else:
                POSE_CONNECTIONS = frozenset([(5, 2), (12, 11), (11, 13), (13, 15), (11, 23), (12, 24),(23,24)])
            if self.results.pose_landmarks:
                    self.mpDraw.draw_landmarks(img, self.results.pose_landmarks, POSE_CONNECTIONS)

        # Image positions of landmarks:
        jointsImgPos = {}
        jointPosMP = {}
        jointsDepthMP=[]
        cantFindPose = []
        if self.results.pose_landmarks:
            h, w, c = img.shape
            for joint_id in objects_to_track:
                joint=self.results.pose_landmarks.landmark[joint_id]
                joint_world=self.results.pose_world_landmarks.landmark[joint_id]
                cx, cy,cz = int(joint.x * w), int(joint.y * h), int(joint.z * w)
                if draw:
                    img = cv2.circle(img, (cx, cy), 8, (255, 0, 0))#, cv2.FILLED)
                    
                if cx<w and cy<h:
                    jointsImgPos[joint_id] = [cx, cy, joint.z,joint.visibility]
                    jointPosMP[joint_id] = [joint_world.x*1000, joint_world.y*1000, joint_world.z*1000,joint_world.visibility]
                    jointsDepthMP.append(joint_world.z*1000)
                else:
                    jointsImgPos[joint_id] = [np.NAN, np.NAN, np.NAN,0]
                    jointPosMP[joint_id] = [np.NAN, np.NAN, np.NAN,0]
                    jointsDepthMP.append(0)
                    cantFindPose.append(True)
        cantFindPose = True if np.sum(np.array(cantFindPose)) > 1 else False
        return jointsImgPos,img,jointPosMP,np.array(jointsDepthMP),cantFindPose
    
    """
    calculate upper length using joint positions from real sense
    """
    def calcUpperLengths(self,jointsPosRS,upperLengthOrder):
        upperLengths = []
        for i,joint_id in enumerate(upperLengthOrder[:-1]):
            curJointPos = np.array(jointsPosRS[upperLengthOrder[i]])[:-1] # just take the x,y,z
            nextJointPos = np.array(jointsPosRS[upperLengthOrder[i+1]])[:-1]
            tgt_limb_length = np.linalg.norm(curJointPos - nextJointPos)/1000
            upperLengths.append(tgt_limb_length)
        # print("Current Sample",np.array([upperLengths]))
        return np.array(upperLengths)
    
    """
    check deviation of upper arm length with calibrated upper arm length
    """
    def checkUpperLengths(self,curUpperLengths,calibUpperLengths):
        # check relative depths for the important joints
        confidence = 0.35
        upper_bound = 1 + confidence
        lower_bound = 1- confidence
        flags = np.logical_or(curUpperLengths > calibUpperLengths*upper_bound, curUpperLengths < calibUpperLengths*lower_bound)
        # print("Calibrated Sample",self.calibUpperLengths)
        if (np.sum(flags) > 0):
            print ("some joints occluded")
            return True
        else:
            return False

"""
Arm IK functions from real sense joints positions
"""
#convenience function returning unit vector from a to b
def unit(from_a, to_b):
    return (to_b-from_a)/np.linalg.norm(to_b-from_a)
#convenience function returning unit vector of vec
def unitV(vec):
    return vec/np.linalg.norm(vec)
def FramesToq(xs, ys, zs, xua, yua, zua, zm, yfa):
    """Performed ISB IK from specific shoulder and UA and forearm frame/vectors
    and return joint angles. Outcome joint angles same as UL arm model (and
    so also the OpenSIM MoBL-ARMS)

    ## Trunk/Shoulder frame:
    # Zs: contralateral to shoulder
    # Ys: orthogonal, through Eyes point (=> ~upward)
    # Xs: resulting, forward

    ## UA (humerus) frame:
    # Yua: along humerus, up: elbow->shoulder
    # Zua: external, out of shoulder-elbow-wrist plane
    # Xua: front forward (i.e. in arm plane)
    # Zm: modified by first rotation: projection of Yua in horizontal shoulder plane (formed by Xs/Zs, with Ys as normal)

    ## Forearm vector
    # Yfa: along radius/cubitus towards wrist
    """

    ## Elbow angle: 0 fully extended, +180 fully flexed
    q_elb = np.pi-np.arccos(np.dot(yua,yfa))

    ## Shoulder angles (almost ISB, different ref and range. ISB sucks):
    q_ele = np.arccos(np.dot(yua,ys)) #Elevation: around Ztransformed, 0 along body, +90 full extended forward (at 0 pel)

    epsilon=np.pi/50 #~<4degrees
    if(q_ele>epsilon):
        q_pel = np.arccos(np.dot(-zs, zm)) #Planele: around Ytrunk: 0 full external, +90 elbow forward, 180 full internal. Computed as angle between Zs(external) and projection of Yua in horizontal shoulder plane (formed by Xs/Zs, with Ys as normal)
    else:
        q_pel = np.NAN #q_pel undefined at 0 elevation

    # Undefined if q_pel is undefined
    if(q_ele>epsilon):
        zm = unitV(zm-np.dot(zm, yua)*yua) #first project zm into Xua/Zua plane
        q_rot = -np.arccos(np.dot(zm, zua))+np.pi/2 #Int/ext rotation: around Ytransformed, angle in plane of normal Yua, between Zua and Zs rotated by pel (aka Zm)
    else:
        #q_rot purely defined based on shoulder-elbow-wrist plane when at 0 elevation: i.e. q_pele is 0
        if(q_elb>epsilon):
            q_rot = np.arccos(np.dot(zs, zua))
        else:
            q_rot = np.NAN #Trully undefined when arm in full extension

    return  q_pel, q_ele, q_rot, q_elb
def IK(jointsPos, arm_side, true_vertical=np.array([]), debug=False):
    """Compute ISB joint angles from MediaPipe joints positions (in mm)
    making some assumptions on true vertical for trunk pose if desired."""

    # Which arm?
    if(arm_side=='l'):
        contra_shoulder=J.R_S
        shoulder=J.L_S
        elbow=J.L_E
        wrist=J.L_W
    else:
        contra_shoulder=J.L_S
        shoulder=J.R_S
        elbow=J.R_E
        wrist=J.R_W

    # Contralateral Shoulder position arrays list
    j=contra_shoulder
    CShoulder=np.array([jointsPos[j][0]/1000., jointsPos[j][1]/1000., jointsPos[j][2]/1000.]).transpose()

    # Shoulder position arrays list (convert to meter)
    j=shoulder
    Shoulder=np.array([jointsPos[j][0]/1000., jointsPos[j][1]/1000., jointsPos[j][2]/1000.]).transpose()

    # Elbow position arrays list
    j=elbow
    Elbow=np.array([jointsPos[j][0]/1000., jointsPos[j][1]/1000., jointsPos[j][2]/1000.]).transpose()

    # Wrist position arrays list
    j=wrist
    Wrist=np.array([jointsPos[j][0]/1000., jointsPos[j][1]/1000., jointsPos[j][2]/1000.]).transpose()

    # Center eyes arrays list
    Eyes=np.array([(jointsPos[J.L_Y][0] + (jointsPos[J.R_Y][0]-jointsPos[J.L_Y][0])/2.)/1000.,
                    (jointsPos[J.L_Y][1] + (jointsPos[J.R_Y][1]-jointsPos[J.L_Y][1])/2.)/1000.,
                    (jointsPos[J.L_Y][2] + (jointsPos[J.R_Y][2]-jointsPos[J.L_Y][2])/2.)/1000.]).transpose()

    ## Trunk frame:
    if(len(true_vertical)==3):
        ## Trunk frame using true vertical:
        # Z: contralateral to shoulder in tranverse plane only (no Y)
        # Y: true vertical: -Y in camera space
        # X: resulting, forward
        zs = unit(CShoulder, Shoulder)
        ys = unitV(true_vertical) #ys is true vertical
        zs = unitV(zs-np.dot(zs,ys)*ys) #no zs component on true vertical
        if(arm_side=='r'):
            xs = np.cross(ys, zs)
        else:
            xs = np.cross(zs, ys) # ISB sucks and doesn't use right hand coordinates on left side
    else:
        # Z: contralateral to shoulder in tranverse
        # Y: through eyes center
        # X: resulting, forward
        zs = unit(CShoulder, Shoulder)
        if(arm_side=='r'):
            xs = unitV(np.cross(unit(Shoulder, Eyes), zs))
            ys = unitV(np.cross(zs, xs))
        else:
            xs = unitV(np.cross(zs, unit(Shoulder, Eyes))) # ISB sucks and doesn't use right hand coordinates on left side
            ys = unitV(np.cross(zs, -xs))

    ## Forearm vector
    # Yfa: along radius/cubitus towards wrist
    yfa = unit(Elbow, Wrist)

    ## UA (humerus) frame:
    # Y: along humerus, up: elbow->shoulder
    # Z: external, out of shoulder-elbow-wrist plane
    # X: forward in elbow-wrist-shoulder plane
    # Zm: transformed by first rotation: projection of yua into Xs/Zs plane
    yua = unit(Elbow, Shoulder)
    if(arm_side=='r'):
        zua = unitV(np.cross(yfa, yua))
        xua = unitV(np.cross(yua, zua))
        zm = unitV(yua-np.dot(yua, ys)*ys)
    else:
        zua = unitV(np.cross(yua, yfa))
        xua = unitV(np.cross(zua, yua)) # ISB sucks and doesn't use right hand coordinates on left side
        zm = unitV(yua-np.dot(yua, ys)*ys)

    if(debug):
        ax = plt.subplots(1,1)
        from spatialmath import SO3, SE3, Plane3
        Ts=SE3([0, 0, 0])*SE3(SO3(np.array([xs, ys, zs]).transpose()))
        ax=Ts.plot(frame='S')
        Tua=SE3([0, 0, 0])*SE3(SO3(np.array([xua, yua, zua]).transpose()))
        Tua.plot(frame='UA', color='green', length=0.5, ax=ax)
        Tm=SE3(Elbow)*SE3(SO3(np.array([unitV(np.cross(ys, zm)), ys, zm]).transpose()))
        Tm.plot(frame='m', color='black', length=0.5, ax=ax)
        Tw=SE3(Wrist)*SE3(SO3(np.array([unitV(np.cross(yfa, zua)), yfa, zua]).transpose()))
        Tw.plot(frame='w', color='black', length=0.5)
        plt.show()

    ## Compute ISB joint angles from frames
    q_pel, q_ele, q_rot, q_elb = FramesToq(xs, ys, zs, xua, yua, zua, zm, yfa)

    return [q_pel, q_ele, q_rot, q_elb]

"""
for signal filtering
# Hold previous times of signals value (i.e. circular buffer) and apply various
# filtering or computation on it
"""
class Signal():
    def __init__(self, first_element, t_first, memory_length):
        self.d = deque([first_element], maxlen=memory_length)
        self.t = deque([t_first], maxlen=memory_length)
        self.dt = -1

    def update(self, element, t):
        self.d.append(element)
        self.t.append(t)
        return self.d

    def setPeriod(self, dt):
        self.dt = dt

    def predictTwoSteps(self, at_t):
        if(len(self.d)>2):
            return np.array(self.d[-1]) + (np.array(self.d[-1])-np.array(self.d[-3]))/(self.t[-1]-self.t[-3])*(at_t-self.t[-1])
        else:
            return self.d[-1]

    def predictOneStep(self, at_t):
        if(len(self.d)>1):
            return np.array(self.d[-1]) + (np.array(self.d[-1])-np.array(self.d[-2]))/(self.t[-1]-self.t[-2])*(at_t-self.t[-1])
        else:
            return self.d[-1]

"""
Start the Pose Detection Thread and Deweighting Thread to calculate joint angles 
"""

#%% for Deweighting GUI
class DeweightThread(QThread):
    ImageUpdate = pyqtSignal(QImage)
    SkeletonUpdate = pyqtSignal(np.ndarray)
    def __init__(self,cameras,flags,rs_datas,mp_datas,server,client,video):
        super().__init__()
        self._run_flag = True
        self.cameras = cameras
        self.flags = flags
        self.rs_datas = rs_datas
        self.mp_datas = mp_datas
        self.server = server
        self.video = video
        self.client = client
        
    def run(self):

        #Arm side to track
        armSide='r'
        # Left eye, Right eye, Left Hip, Right Hip, Left Shoulder, Right Shoulder, Left Elbow, Left Wrist
        if armSide == 'l':
            objects_to_track = [J.L_Y, J.R_Y, J.L_H, J.R_H, J.L_S, J.R_S, J.L_E, J.L_W]
            upperLengthsOrder = [J.R_S, J.L_S, J.L_E, J.L_W]
        elif armSide == 'r':
            objects_to_track = [J.L_Y, J.R_Y, J.L_H, J.R_H, J.L_S, J.R_S, J.R_E, J.R_W]
            upperLengthsOrder = [J.L_S, J.R_S, J.R_E, J.R_W]

        pTime = 0
        startTime = time.time()
        fps = 0
        final_fps = 30
        detector = PoseDetector()
        depthS = Signal(np.array([0 for j in objects_to_track]), 0, 3)

        # for arm length calibration for wrist occlusion
        calibTime = time.time()
        calibPeriod = 10
        calibCount = 0
        self.calibUpperLengths = np.zeros((1, 3))
        upperLengths = np.zeros((1, 3))
        calibrated = False
        startCalibrate = False

        """
        initialization for data collection
        """
        # sub_dirs_in_btwn = ["mo_cap"]
        # target_folder = "depth_cam"
        cur_cwd = os.getcwd() #change_cwd_until_folder(sub_dirs_in_btwn,target_folder)
        self.traj_path = os.path.join(os.path.join(cur_cwd,"subject_data_depth_cam"),"traj")
        self.body_param_path = os.path.join(os.path.join(cur_cwd,"subject_data_depth_cam"),"body_param")
        subject_files = list_files_in_folder(self.traj_path)
        print("Subject files in folder:", subject_files)
        if not subject_files:
            self.cur_sbjject_number = 0
        else:
            self.cur_sbjject_number = find_latest_subject_num(subject_files)+1
        self.file_name = f"s{self.cur_sbjject_number}_{armSide}.csv"
        self.subject_data = []

        """
        flag to detect submovement
        """
        def on_press_reaction(event):
            global submovement
            if event.name == 'a':
                submovement = submovement + 1
                print(f"SubMovement: {submovement}")
        keyboard.on_release(on_press_reaction)

        while self._run_flag:            
            fps = fps + 1
            cTime = time.time()

            if (cTime-pTime > 1.0):
                final_fps = fps
                fps = 0
                pTime = cTime

            """
            Capture Camera Feed and get joint position in image coordinates
            """
            if(self.cameras[0].init):
                # Capture Camera Frame
                ret, color_image, depth_image = self.cameras[0].get_frame_stream()
                # copy
                frame = color_image.copy()
                color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
            else:
                # Webcam otherwise
                success, frame = self.cameras[1].read()
                color_image = frame

            # frame is writeable
            frame.flags.writeable = True
            ## Get landmarks image position
            jointsPosImg,self.img,jointsPosMP,_,cantFindPose = detector.findPose(frame, armSide, objects_to_track, self.flags[0])

            """
            Get joint position in 3D space from real sense
            check occlusion by checking current upper arm length with calibrated upper arm length
            """
            if(self.cameras[0].init and len(jointsPosImg)>0):
                ## Convert to 3D and do real time plotting
                jointsPos,_,_ = self.cameras[0].imgTo3D(jointsPosImg, depth_image)
                q_no_detect = IK(jointsPos, armSide)
                curUpperLengths = detector.calcUpperLengths(jointsPos,upperLengthsOrder)
                jointsOccluded = detector.checkUpperLengths(curUpperLengths,self.calibUpperLengths)

                # conditions for calibration and reset when calibration is disrupted
                if not calibrated:
                    if startCalibrate:
                        self.img = cv2.putText(self.img,f"{(cTime - calibTime):.4f} - Calibration, keep still ",(50,100),cv2.FONT_HERSHEY_COMPLEX,1,(255,255,255),2,cv2.LINE_AA)
                        if cantFindPose or np.sum(np.isnan(curUpperLengths)) > 0:
                            startCalibrate = False
                            print("Restart the calibration")
                            self.img = cv2.putText(self.img,"Pls make sure all landmarks can be seen",(50,100),cv2.FONT_HERSHEY_COMPLEX,1,(0,0,255),2,cv2.LINE_AA)
                            calibTime = cTime
                            calibCount = 0
                            self.calibUpperLengths = np.zeros((1, 3))
                            upperLengths = np.zeros((1, 3))
                        else:
                            if (cTime - calibTime) < calibPeriod:
                                calibCount = calibCount + 1
                                upperLengths = upperLengths + curUpperLengths# cur sample humerus length
                                self.calibUpperLengths = upperLengths/calibCount
                            else:
                                calibrated = True
                    else:
                        if cantFindPose or np.sum(np.isnan(curUpperLengths)) > 0:
                            startCalibrate = False
                            print("Restart the calibration")
                            self.img = cv2.putText(self.img,"Pls make sure all landmarks can be seen and not",(50,100),cv2.FONT_HERSHEY_COMPLEX,1,(0,0,255),2,cv2.LINE_AA)
                            calibTime = cTime
                            calibCount = 0
                            self.calibUpperLengths = np.zeros((1, 3))
                            upperLengths = np.zeros((1, 3))
                        else:
                            startCalibrate = True
                else:
                    self.img = cv2.putText(self.img,"Calibrated",(50,100),cv2.FONT_HERSHEY_COMPLEX,0.7,(0,255,0),2,cv2.LINE_AA)
                    self.img = cv2.putText(self.img,f"Calibrated Arm: {self.calibUpperLengths}",(50,125),cv2.FONT_HERSHEY_COMPLEX,0.7,(0,255,0),2,cv2.LINE_AA)
                    self.img = cv2.putText(self.img,f"Current Arm: {curUpperLengths}",(50,150),cv2.FONT_HERSHEY_COMPLEX,0.7,(0,255,0),2,cv2.LINE_AA)
                    self.img = cv2.putText(self.img,f"time: {(cTime-startTime-calibPeriod):.4f}",(50,75),cv2.FONT_HERSHEY_COMPLEX,1,(255,255,255),2,cv2.LINE_AA)
                    self.img = cv2.putText(self.img,f"Movement: {submovement}",(50,175),cv2.FONT_HERSHEY_COMPLEX,1,(255,255,255),2,cv2.LINE_AA)

                """
                Check joint occlusion and correct the joint angles
                """
                if jointsOccluded:
                    q = IK(jointsPosMP, armSide)
                    self.img = cv2.putText(self.img,"Occlusion",(50,75),cv2.FONT_HERSHEY_COMPLEX,1,(255,0,0),2,cv2.LINE_AA)
                else:
                    q = IK(jointsPos, armSide)

                """
                Collect Data after calibration is finished
                """
                if calibrated:
                    # print(jointsPos[upperLengthsOrder[1]][:-1])
                    # print([cTime]+jointsPos[upperLengthsOrder[1]][:-1]+jointsPos[upperLengthsOrder[2]][:-1]+jointsPos[upperLengthsOrder[3]][:-1]+q)
                    self.subject_data.append([final_fps]+[cTime-startTime-calibPeriod]+jointsPos[upperLengthsOrder[1]][:-1]+jointsPos[upperLengthsOrder[2]][:-1]+jointsPos[upperLengthsOrder[3]][:-1]+q+[submovement])
                print("Q: ",q)

                """
                For Visualization Purposes
                """
                if(self.flags[0]):
                    if np.sum(np.isnan(q_no_detect)) < 1: # only attach "valid" joint angles
                        timestamp = time.time()
                        for index, rs_data in enumerate(self.rs_datas):
                            rs_data.cb_append_data_point(q[index]*180/np.pi, timestamp)
                        for index, mp_data in enumerate(self.mp_datas):
                            mp_data.cb_append_data_point(q_no_detect[index]*180/np.pi, timestamp)

                        if calibrated:
                            if jointsOccluded:
                                color = (0,0,255)
                            else:
                                color = (0,255,0)
                            for i,joint_id in enumerate(objects_to_track):
                                try:
                                    left = [J.L_Y, J.L_H, J.L_S,  J.L_E, J.L_W]
                                    right = [ J.R_Y,  J.R_H, J.R_S, J.R_E, J.R_W]
                                    if joint_id in left:
                                        spacing = 100
                                    elif joint_id in right:
                                        spacing = -100

                                    if joint_id ==  J.L_E:
                                        spacing = 100
                                    elif joint_id == J.L_W:
                                        spacing = -100
                                    # self.img = cv2.putText(self.img,f"{joint_id}: x:{jointsPosMP[joint_id][0]:.2f},   {jointsPos[joint_id][0]:.2f}",(jointsPosImg[joint_id][0]+spacing,jointsPosImg[joint_id][1]+20),cv2.FONT_HERSHEY_COMPLEX,0.7,color,1,cv2.LINE_AA)
                                    # self.img = cv2.putText(self.img,f"{joint_id}: y:{jointsPosMP[joint_id][1]:.2f},   {jointsPos[joint_id][1]:.2f}",(jointsPosImg[joint_id][0]+spacing,jointsPosImg[joint_id][1]+40),cv2.FONT_HERSHEY_COMPLEX,0.7,color,1,cv2.LINE_AA)
                                    # self.img = cv2.putText(self.img,f"{joint_id}: z:{jointsPosMP[joint_id][2]:.2f},   {jointsPos[joint_id][2]:.2f}",(jointsPosImg[joint_id][0]+spacing,jointsPosImg[joint_id][1]+60),cv2.FONT_HERSHEY_COMPLEX,0.7,color,1,cv2.LINE_AA)
                                    # self.img = cv2.putText(self.img,f"{joint_id}: d:{jointsPosMP[joint_id][-1]:.2f},   {jointsPos[joint_id][-1]:.2f}",(jointsPosImg[joint_id][0]+spacing,jointsPosImg[joint_id][1]+80),cv2.FONT_HERSHEY_COMPLEX,0.7,color,1,cv2.LINE_AA)
                                except:
                                    print(jointsPosMP[joint_id])   
                                    print(jointsPos[joint_id]) 
                    else:
                        timestamp = time.time()
                        for index, rs_data in enumerate(self.rs_datas):
                            rs_data.cb_append_data_point(0, timestamp)
                        for index, mp_data in enumerate(self.mp_datas):
                            mp_data.cb_append_data_point(q_no_detect[index]*180/np.pi, timestamp)

                self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
                self.img = cv2.putText(self.img,f"{final_fps}",(50,50),cv2.FONT_HERSHEY_COMPLEX,1,(255,0,0),2,cv2.LINE_AA)
                self.img = QImage(self.img.data, self.img.shape[1], self.img.shape[0], QImage.Format.Format_RGB888)
                self.img = self.img.scaled(640, 360, Qt.AspectRatioMode.KeepAspectRatio)
                self.ImageUpdate.emit(self.img)
            else:
                if not calibrated: # if not all limbs are detected and not yet calibrated, dont start the time for calibration
                    calibTime = cTime
                    startCalibrate = False
                    print("Dont start the calibration")

            """
            Run Streaming to FLNL or Serial
            """
            if(self.flags[3]):
                if(self.flags[1]):
                    self.video.write(color_image)

                if len(jointsPosImg)>0:
                    # val = []
                    # if armSide=='l':
                    #     val.append(0.0)
                    # else:
                    #     val.append(1.0)
                    # for id in objects_to_track:
                    #     val.append(jointsPos[id][0])
                    #     val.append(jointsPos[id][1])
                    #     val.append(jointsPos[id][2])
                    if(self.flags[2]):
                        np.set_printoptions(precision=2)
                        np.set_printoptions(suppress=True)
                        print("Streaming",final_fps)
                        print()
                    else:
                        if calibrated:
                            # self.server.SendValues(val)
                            cmd_type = "DWF"
                            self.client.SendCmd(cmd_type,[0,0,0])
                            print("Sending",final_fps)
                            print()

            """
            Process FLNL Incoming Commands
            """
            if(not self.flags[2]):
                """
                connected
                """
                ## Start streaming?
                if(self.server.IsCmd("STA")):
                    self.flags[3]=True
                    print("Start streaming values")
                    if(self.cameras[0] and self.flags[1]):
                        self.cameras[0].recorder.resume()
                        print("Start recording stream")

                ## Stop streaming?
                if(self.server.IsCmd("STO")):
                    self.flags[3]=False
                    print("Stop streaming values")
                    if(self.cameras[0].init and self.flags[1]):
                        self.cameras[0].recorder.pause()
                        print("Stop recording stream")

                ## Set to left arm
                if(self.server.IsCmd("ARL")):
                    armSide='l'
                    # Left eye, Right eye, Left Hip, Right Hip, Left Shoulder, Right Shoulder, Left Elbow, Left Wrist
                    objects_to_track = [J.L_Y, J.R_Y, J.L_H, J.R_H, J.L_S, J.R_S, J.L_E, J.L_W]
                    upperLengthsOrder = [J.R_S, J.L_S, J.L_E, J.L_W]
                    calibTime = cTime
                    calibCount = 0
                    self.calibUpperLengths = np.zeros((1, 3))
                    upperLengths = np.zeros((1, 3))
                    calibrated = False  
                    self.subject_data = []
                    startCalibrate = False    
                    startTime = 0    
                    print("Tracking LEFT arm")

                ## Set to right arm
                if(self.server.IsCmd("ARR")):
                    armSide='r'
                    # Left eye, Right eye, Left Hip, Right Hip, Left Shoulder, Right Shoulder, Right Elbow, Right Wrist
                    objects_to_track = [J.L_Y, J.R_Y, J.L_H, J.R_H, J.L_S, J.R_S, J.R_E, J.R_W]
                    upperLengthsOrder = [J.L_S, J.R_S, J.R_E, J.R_W]
                    calibTime = cTime
                    calibCount = 0
                    self.calibUpperLengths = np.zeros((1, 3))
                    upperLengths = np.zeros((1, 3))
                    calibrated = False
                    self.subject_data = []
                    startCalibrate = False
                    startTime = 0  
                    print("Tracking RIGHT arm")
                ## Disconnect command
                if(self.server.IsCmd("DIS")):
                    self._run_flag = False
            else:
                """
                Process Incoming Commands if not connected
                """
                ## For testing when not connected
                ## Start streaming? 
                if keyboard.is_pressed('t'):
                    self.flags[3]=True
                    print("Start streaming values")
                    if(self.cameras[0] and self.flags[1]):
                        self.cameras[0].recorder.resume()
                        print("Start recording stream")

                ## Stop streaming?
                if keyboard.is_pressed('s'):
                    self.flags[3]=False
                    print("Stop streaming values")
                    if(self.cameras[0].init and self.flags[1]):
                        self.cameras[0].recorder.pause()
                        print("Stop recording stream")

                ## Set to left arm
                if keyboard.is_pressed('l'):
                    armSide='l'
                    # Left eye, Right eye, Left Hip, Right Hip, Left Shoulder, Right Shoulder, Left Elbow, Left Wrist
                    objects_to_track = [J.L_Y, J.R_Y, J.L_H, J.R_H, J.L_S, J.R_S, J.L_E, J.L_W]
                    upperLengthsOrder = [J.R_S, J.L_S, J.L_E, J.L_W]
                    calibTime = cTime
                    calibCount = 0
                    self.calibUpperLengths = np.zeros((1, 3))
                    upperLengths = np.zeros((1, 3))
                    calibrated = False  
                    startCalibrate = False
                    self.subject_data = []
                    self.file_name = f"s{self.cur_sbjject_number}_{armSide}.csv"
                    startTime = 0  
                    print("Tracking LEFT arm")

                ## Set to right arm
                if keyboard.is_pressed('r'):
                    armSide='r'
                    # Left eye, Right eye, Left Hip, Right Hip, Left Shoulder, Right Shoulder, Right Elbow, Right Wrist
                    objects_to_track = [J.L_Y, J.R_Y, J.L_H, J.R_H, J.L_S, J.R_S, J.R_E, J.R_W]
                    upperLengthsOrder = [J.L_S, J.R_S, J.R_E, J.R_W]
                    calibTime = cTime
                    calibCount = 0
                    self.calibUpperLengths = np.zeros((1, 3))
                    upperLengths = np.zeros((1, 3))
                    calibrated = False
                    startCalibrate = False
                    self.subject_data = []
                    self.file_name = f"s{self.cur_sbjject_number}_{armSide}.csv"
                    startTime = 0  
                    print("Tracking RIGHT arm")

                #Turn drawing on/off
                if keyboard.is_pressed('d'):
                    self.flags[0] = not self.flags[0]

            """
            Close
            """
            # Can also close with 'q'
            if  keyboard.is_pressed('q'):
                # shut down capture system
                self._run_flag = False
            
    def stop(self):
        """
        Sets run flag to False and waits for thread to finish
        """
        # Create a DataFrame
        traj = pd.DataFrame(self.subject_data, columns=['fps','time','x_shld','y_shld','z_shld','x_elbw','y_elbw','z_elbw','x_wrst','y_wrst','z_wrst','q1', 'q2', 'q3', 'q4',"submvmt"])
        calibUpperLengths = self.calibUpperLengths.tolist()
        body = pd.DataFrame(calibUpperLengths, columns=["shoulder","ua","fa"])
        # Write the DataFrame to a CSV file to the subject_data folder
        traj.to_csv(os.path.join(self.traj_path,self.file_name), index=False)
        body.to_csv(os.path.join(self.body_param_path,self.file_name), index=False)
        self._run_flag = False

        ## Wait for disconnection
        print("Disconnected. Exiting...")

        ## Exit
        self.flags[3]=False
        if(not self.flags[2]):
            if(self.server.IsConnected()):
                self.server.Close()
            if self.client.IsConnected():
                self.client.Close()
        if(self.cameras[0].init):
            if(self.flags[1]):
                self.cameras[0].recorder.pause()
                self.video.release()
            self.cameras[0].release()
        else:
            self.cameras[1].release()
        return 0

class DeweightApp(QWidget):
    def __init__(self,cameras,flags,server,client,video):
        super().__init__()
        self.setWindowTitle("Deweighting GUI")
        DWGUI = QtWidgets.QHBoxLayout()

        """
        UA kinematic Widget
        """
        joint_angle_widget = pg.LayoutWidget()
        self.rs_datas = []
        poe_widget = LivePlotWidget(title=f"UA Plane of Elevation",
                                x_range_controller=LiveAxisRange(roll_on_tick=250),
                                y_range_controller=LiveAxisRange(fixed_range=[-10, 190])
                                )
        poe = LiveLinePlot(pen="yellow")
        poe.set_leading_line(LeadingLine.HORIZONTAL, pen=mkPen("yellow"), text_axis=LeadingLine.AXIS_Y)
        poe_widget.addItem(poe)
        self.rs_datas.append(DataConnector(poe, max_points=300))
        joint_angle_widget.addWidget(poe_widget, row=0, col=0,rowspan=1,colspan=1)

        elevation_widget = LivePlotWidget(title=f"Elevation",
                                x_range_controller=LiveAxisRange(roll_on_tick=250),
                                y_range_controller=LiveAxisRange(fixed_range=[-10, 100]))
        elevation = LiveLinePlot(pen="yellow")
        elevation.set_leading_line(LeadingLine.HORIZONTAL, pen=mkPen("yellow"), text_axis=LeadingLine.AXIS_Y)
        elevation_widget.addItem(elevation)
        self.rs_datas.append(DataConnector(elevation, max_points=300))
        joint_angle_widget.addWidget(elevation_widget, row=1, col=0,rowspan=1,colspan=1)

        ie_rot_widget = LivePlotWidget(title="I/E Rotation",
                                            x_range_controller=LiveAxisRange(roll_on_tick=250),
                                            y_range_controller=LiveAxisRange(fixed_range=[-190, 190]))
        ie_rot = LiveLinePlot(pen="yellow")
        ie_rot.set_leading_line(LeadingLine.HORIZONTAL, pen=mkPen("yellow"), text_axis=LeadingLine.AXIS_Y)
        ie_rot_widget.addItem(ie_rot)
        self.rs_datas.append(DataConnector(ie_rot, max_points=300))
        joint_angle_widget.addWidget(ie_rot_widget, row=2, col=0,rowspan=1,colspan=1)

        ext_flex_left_axis = LiveAxis("left", axisPen="red", textPen="red")
        ext_flex_bottom_axis = LiveAxis("bottom", axisPen="green", textPen="green", **{Axis.TICK_FORMAT: Axis.TIME})
        ext_flex_widget = LivePlotWidget(title="Ext/Flex",
                                            axisItems={'bottom': ext_flex_bottom_axis, 'left': ext_flex_left_axis},
                                            x_range_controller=LiveAxisRange(roll_on_tick=250),
                                            y_range_controller=LiveAxisRange(fixed_range=[-10, 190]))
        ext_flex = LiveLinePlot(pen="yellow")
        ext_flex.set_leading_line(LeadingLine.HORIZONTAL, pen=mkPen("yellow"), text_axis=LeadingLine.AXIS_Y)
        ext_flex_widget.addItem(ext_flex)
        self.rs_datas.append(DataConnector(ext_flex, max_points=300))
        joint_angle_widget.addWidget(ext_flex_widget, row=3, col=0,rowspan=1,colspan=1)
        joint_angle_widget.setFixedSize(360,720)

        """
        UA kinematic Widget No Detect
        """
        joint_angle_widget_no_detect = pg.LayoutWidget()
        self.mp_datas = []
        poe_widget = LivePlotWidget(title=f"UA Plane of Elevation No Detect",
                                x_range_controller=LiveAxisRange(roll_on_tick=250),
                                y_range_controller=LiveAxisRange(fixed_range=[-10, 190])
                                )
        poe_mp = LiveLinePlot(pen="white")
        poe_mp.set_leading_line(LeadingLine.HORIZONTAL, pen=mkPen("white"), text_axis=LeadingLine.AXIS_Y)
        poe_widget.addItem(poe_mp)
        self.mp_datas.append(DataConnector(poe_mp, max_points=300))
        joint_angle_widget_no_detect.addWidget(poe_widget, row=0, col=0,rowspan=1,colspan=1)

        elevation_widget = LivePlotWidget(title=f"Elevation No Detect",
                                x_range_controller=LiveAxisRange(roll_on_tick=250),
                                y_range_controller=LiveAxisRange(fixed_range=[-10, 100]))
        elevation_mp = LiveLinePlot(pen="white")
        elevation_mp.set_leading_line(LeadingLine.HORIZONTAL, pen=mkPen("white"), text_axis=LeadingLine.AXIS_Y)
        elevation_widget.addItem(elevation_mp)
        self.mp_datas.append(DataConnector(elevation_mp, max_points=300))
        joint_angle_widget_no_detect.addWidget(elevation_widget, row=1, col=0,rowspan=1,colspan=1)

        ie_rot_widget = LivePlotWidget(title="I/E Rotation No Detect",
                                            x_range_controller=LiveAxisRange(roll_on_tick=250),
                                            y_range_controller=LiveAxisRange(fixed_range=[-190, 190]))
        ie_rot_mp = LiveLinePlot(pen="white")
        ie_rot_mp.set_leading_line(LeadingLine.HORIZONTAL, pen=mkPen("white"), text_axis=LeadingLine.AXIS_Y)
        ie_rot_widget.addItem(ie_rot_mp)
        self.mp_datas.append(DataConnector(ie_rot_mp, max_points=300))
        joint_angle_widget_no_detect.addWidget(ie_rot_widget, row=2, col=0,rowspan=1,colspan=1)

        ext_flex_left_axis = LiveAxis("left", axisPen="red", textPen="red")
        ext_flex_bottom_axis = LiveAxis("bottom", axisPen="green", textPen="green", **{Axis.TICK_FORMAT: Axis.TIME})
        ext_flex_widget = LivePlotWidget(title="Ext/Flex No Detect",
                                            axisItems={'bottom': ext_flex_bottom_axis, 'left': ext_flex_left_axis},
                                            x_range_controller=LiveAxisRange(roll_on_tick=250),
                                            y_range_controller=LiveAxisRange(fixed_range=[-10, 190]))
        ext_flex_mp = LiveLinePlot(pen="white")
        ext_flex_mp.set_leading_line(LeadingLine.HORIZONTAL, pen=mkPen("white"), text_axis=LeadingLine.AXIS_Y)
        ext_flex_widget.addItem(ext_flex_mp)
        self.mp_datas.append(DataConnector(ext_flex_mp, max_points=300))
        joint_angle_widget_no_detect.addWidget(ext_flex_widget, row=3, col=0,rowspan=1,colspan=1)
        joint_angle_widget_no_detect.setFixedSize(360,720)


        """
        RealSense Video Widget
        """
        self.disply_width = 640
        self.display_height = 360
        self.CameraFeed = QLabel('label1')
        self.CameraFeed.resize(self.disply_width, self.display_height)

        DWGUI.addWidget(joint_angle_widget)
        DWGUI.addWidget(self.CameraFeed)
        DWGUI.addWidget(joint_angle_widget_no_detect)
        
        self.setLayout(DWGUI)

        # create the video capture thread and sampling thread
        self.dw_thread = DeweightThread(cameras,flags,self.rs_datas,self.mp_datas,server,client,video)
        # connect its signal to the update_image slot
        self.dw_thread.ImageUpdate.connect(self.ImageUpdateSlot)
        # start the thread
        self.dw_thread.start()

    def ImageUpdateSlot(self, Image):
        self.CameraFeed.setPixmap(QPixmap.fromImage(Image))

    def closeEvent(self, event):
        print(self.dw_thread.stop())
        event.accept()
