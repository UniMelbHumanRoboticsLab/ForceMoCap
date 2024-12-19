# -*- coding: utf-8 -*-
"""
Created on Mon May  6 15:46:58 2024

Class of deweighting algorithms intended for use with EMU robot (i.e. force
only applied at the wrist/hand) and an ISB 7 DoF arm model define with the
 robotics toolbox.

@author: vcrocher - Unimelb
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation as R
import pandas as pd
import sys,os
sys.path.append(os.path.join(os.path.dirname(__file__)))
from ISBUL import *

class arm_xsens():
    def __init__(self, body_params={'torso':0.5,'clav':0.2,'ua_l': 0.3, 'fa_l': 0.25, 'ha_l': 0.1, 'm_ua': 2.0, 'm_fa':1.1+0.23+0.6},model='xsens',arm_side=True):

        self.model = model
        #Handle simple initialisation with overall bidy mass instead of hand, FA and UA masses
        # if 'm_body' in body_params:
        #     #7 Dof arm model without masses
        #     self.UL = isb_ul_10dof(body_params['ua_l'],
        #                                 body_params['fa_l'],
        #                                 body_params['ha_l'])
        #     #set masses from body mass
        #     self.ArmMassFromBodyMass(body_params['m_body'])
        # #Or init with individual segment masses:
        # else:
        if self.model == 'xsens':
            self.UL = xsens_ul_12dof(body_params['torso'],
                                     body_params['clav'],
                                     body_params['ua_l'],
                                     body_params['fa_l'],
                                     body_params['ha_l'],
                                     body_params['m_ua'],
                                     body_params['m_fa'],
                                     arm_side=arm_side)

        # dominant hand
        self.cur_side = arm_side
        
        #Overall arm mass
        self.Marm=0
        for l in self.UL.links:
            self.Marm+=l.m

        #Default gravity vector (can be changed)
        self.UL.gravity=[0,0,-9.81]
        
    """
    Estimate new joint angles (task parameters) from new task points
    - TODO: develop an IK that can recreate that without giving the explicit joint angles 
    """
    def IK_task_params(self,task_points,joints_traj,point_index,visual_ik):
        qq_new = []
        qq_new.append(joints_traj.values[point_index[0]]) # initial configuration
        for i,task_point in enumerate(task_points):
            TT=SE3(task_point)
            iter = 0
            success=0
            while (success == 0 and iter < 3):
                iter = iter+1
                # To replace with a custom IK that follows healthy body constraints
                q0 = np.array(joints_traj.values[point_index[i+1]].tolist())
                qq, success, iterations, searches, residual=self.UL.ik_GN(TT, q0=q0, mask=[1, 1, 1, 1, 1, 1],tol=1e-6,pinv=True)
            qq_new.append(qq)
            if success == 0:
                assert 0
            print(f"Success / Iterations/ Searches:",success,iterations,searches)
            print("Intended Task Param:",q0*180/np.pi,"\nCalculated Task Param:",qq*180/np.pi)
            print("Actual Task Point:",task_point.t)
            print("Assumed Task Point:",self.UL.fkine(q0).t)
            print("Estimated Task Point:",self.UL.fkine(qq).t)
            print()

        qq_new.append(joints_traj.values[point_index[-1]-1]) # take the one just before resting submovement
        if visual_ik:
            fig = plt.figure()
            self.UL.plot(q = np.array(qq_new),
                        backend='pyplot',block=False,loop=False,jointaxes=True,eeframe=True,shadow=False,fig=fig,dt=3)
            for qq in qq_new:
                robot_joints=self.UL.fkine_all(np.array(qq)) # this has all the frames of the robot joints
                robot_ee = self.UL.fkine(np.array(qq))
                self.plot_joints_ee_frames(robot_joints,robot_ee)
            
        qq_new = pd.DataFrame(qq_new, columns=list(joints_traj.columns))
        return qq_new
    
    def plot_joints_ee_frames(self,robot_joints,robot_ee):
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1,projection='3d')
        ax.set_xlim(-0.5,0.5)
        ax.set_ylim(-0.5,0.5)
        ax.set_zlim(-0.5,0.5)
        ax.set_box_aspect([1, 1, 1])

        x = np.array([robot_joints[0].t[0],robot_joints[4].t[0],robot_joints[6].t[0],robot_joints[8].t[0],robot_joints[10].t[0]])
        y = np.array([robot_joints[0].t[1],robot_joints[4].t[1],robot_joints[6].t[1],robot_joints[8].t[1],robot_joints[10].t[1]])
        z = np.array([robot_joints[0].t[2],robot_joints[4].t[2],robot_joints[6].t[2],robot_joints[8].t[2],robot_joints[10].t[2]])
        ax.plot(x,y,z,marker='o', linestyle='-', color='k')
        import matplotlib.colors as mcolors
        colors = list(mcolors.TABLEAU_COLORS.values())+list(mcolors.TABLEAU_COLORS.values())

        for i,robot_joint_pose in enumerate(robot_joints):
            if i == 0 :
                off = np.array([0.0,0.0,0.0])
            else:   
                off = np.array([0.02,-0.02,-0.02])
            offset = SE3.Rt(robot_joint_pose.R, robot_joint_pose.t+robot_joint_pose.R@off)
            offset.plot(frame=f"{i}", length=0.05, ax=ax,color=colors[i],flo=(0.005,0.005,0.005))
        robot_ee.plot(frame=f"hand", length=0.05, ax=ax,color='k',flo=(0.01,0.01,0.01))
        
    def ArmMassFromBodyMass(self, body_mass: float):
        '''Calculate arm mass from overall body mass based on anthropomorphic rules
        from Drillis et al., Body Segment Parameters, 1964. Table 7'''
        UA_percent_m = 0.053
        FA_percent_m = 0.036
        hand_percent_m = 0.013
        self.UL[2].m = UA_percent_m*body_mass
        self.UL[4].m = (FA_percent_m+hand_percent_m)*body_mass
        self.Marm=0
        for l in self.UL.links:
            self.Marm+=l.m

    def SetGravity(self,g_vector: np.array =[0,0,-9.81]):
        '''Define (set) gravitational vector of the model'''
        self.UL.gravity=g_vector
