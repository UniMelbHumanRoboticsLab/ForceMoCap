from spatialmath import SE3,SO3,Plane3
from scipy.spatial.transform import Rotation as R
import numpy as np
import matplotlib.pyplot as plt
from enum import IntEnum
import matplotlib.colors as mcolors
from itertools import product
from tqdm import tqdm
np.set_printoptions(suppress=True,precision=4) # suppress scientific notation

import sys,os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from isbul_pckg.isbulmodel.arm_lfd import arm_lfd

def plotJointFrames_EE(robot_joints,robot_ee):

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
    colors = list(mcolors.TABLEAU_COLORS.values())+list(mcolors.TABLEAU_COLORS.values())

    for i,robot_joint_pose in enumerate(robot_joints):
        if i == 0 :
            off = np.array([0.0,0.0,0.0])
        else:   
            off = np.array([0.02,-0.02,-0.02])
        offset = SE3.Rt(robot_joint_pose.R, robot_joint_pose.t+robot_joint_pose.R@off)
        offset.plot(frame=f"{i}", length=0.05, ax=ax,color=colors[i],flo=(0.005,0.005,0.005))
    robot_ee.plot(frame=f"hand", length=0.05, ax=ax,color='k',flo=(0.01,0.01,0.01))
    

#Define ISB rtb arm model
body_params = {'torso':0.6,
                      'clav': 0.4,
                      'ua_l': 0.3,
                      'fa_l': 0.25,
                      'ha_l': 0.05,
                      'm_ua': 2.0,
                      'm_fa': 1.1+0.23+0.6}
ul_model = arm_lfd(body_params,model="xsens",arm_side="right")
ul_model_left = arm_lfd(body_params,model="xsens",arm_side="left")

"""
Test FA and UA
"""
ul_posture_to_test = [[0,0,0,0,0,0,0,0,0,0,0,0]]

plot = True
for ul_posture in tqdm(ul_posture_to_test):
    #Compute theoretical link positions for each posture
    robot_joints=ul_model.UL.fkine_all(np.deg2rad(np.array(ul_posture))) # this has all the frames of the robot joints
    robot_ee = ul_model.UL.fkine(np.deg2rad(np.array(ul_posture)))
    plotJointFrames_EE(robot_joints,robot_ee)
    plt.show(block=False)
    robot_joints=ul_model_left.UL.fkine_all(np.deg2rad(np.array(ul_posture))) # this has all the frames of the robot joints
    robot_ee = ul_model_left.UL.fkine(np.deg2rad(np.array(ul_posture)))
    plotJointFrames_EE(robot_joints,robot_ee)
    plt.show(block=True)
    # ul_model.UL.plot(np.deg2rad(np.array(ul_posture)),block=False)
    
    