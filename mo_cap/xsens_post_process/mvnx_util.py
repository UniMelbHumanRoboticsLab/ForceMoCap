import numpy as np

import sys,os
sys.path.append(os.path.join(os.path.dirname(__file__)))
from load_mvnx import load_mvnx

def convert_mvn_to_isb_angles(file_name,side):
    # Load data
    mvnx_file = load_mvnx(file_name)

    # Extract relevant joint angles and convert them to the ISBUL representation. Ignore wrist for now (not in our dataset)
    #get_joint_angle(id)	1x3 vector (x, y, z)	degrees [deg]	Euler representation of the joint angle calculated using the Euler sequence ZXY using the ISB based coordinate system.
    #get_joint_angle_xzy(id)	1x3 vector (x, y, z)	degrees [deg]	Euler representation of the joint angle calculated using the Euler sequence XZY using the ISB based coordinate system.
    #Note: The joint angle using Euler sequence XZY is calculated and exported for all joints, but commonly only used for the shoulder joints, and it may depend on the movement of the shoulder if it is appropriate to use.
    #get_point_pos: position of the anatomical points but no index-name available...

    ##### Joints list (from mvn.py)
    JOINT_RIGHT_T4_SHOULDER = 6
    JOINT_RIGHT_SHOULDER = 7
    JOINT_RIGHT_ELBOW = 8
    JOINT_RIGHT_WRIST = 9
    JOINT_LEFT_T4_SHOULDER = 10
    JOINT_LEFT_SHOULDER = 11
    JOINT_LEFT_ELBOW = 12
    JOINT_LEFT_WRIST = 13

    ##### Ergo Joints list (from mvn.py)
    ERGO_JOINT_VERTICAL_T8 = 5

    #Joints mapping to obtain a 12DoF arm list of angles
    #each dof is described as:
         # - an MVN joint (see list above)
         # - type of euler angle to apply
         # - euler angle idx (0:x, 1:y, 2:z)
         # - multiplier (commonly to convert from deg to rad)
         # - offset
    if side == 'right':
        j_map =[[ERGO_JOINT_VERTICAL_T8,'zxy', 1,   'Ergo'], # trunk_ie
                [ERGO_JOINT_VERTICAL_T8,'zxy', 0,   'Ergo'], # trunk_aa
                [ERGO_JOINT_VERTICAL_T8,'zxy', 2,   'Ergo'], # trunk_fe
                [JOINT_RIGHT_T4_SHOULDER,'zxy', 2,   'Euler'], # scapula_de
                [JOINT_RIGHT_T4_SHOULDER,'zxy', 1,   'Euler'], # scapula_pr
                [JOINT_RIGHT_SHOULDER,  'zxy', 2,   'Euler'], # shoulder_fe
                [JOINT_RIGHT_SHOULDER,  'zxy', 0,   'Euler'], # shoulder_aa
                [JOINT_RIGHT_SHOULDER,  'zxy', 1,   'Euler'], # shoulder_ie
                [JOINT_RIGHT_ELBOW,     'zxy', 2,   'Euler'], # elbow_fe
                [JOINT_RIGHT_ELBOW,     'zxy', 1,   'Euler'], # elbow_ps
                [JOINT_RIGHT_WRIST,     'zxy', 2,   'Euler'], # wrist_fe
                [JOINT_RIGHT_WRIST,     'zxy', 0,   'Euler']] # wrist_dev
    else:
        j_map =[[ERGO_JOINT_VERTICAL_T8,'zxy', 1,   'Ergo'], # trunk_ie
                [ERGO_JOINT_VERTICAL_T8,'zxy', 0,   'Ergo'], # trunk_aa
                [ERGO_JOINT_VERTICAL_T8,'zxy', 2,   'Ergo'], # trunk_fe
                [JOINT_LEFT_T4_SHOULDER,'zxy', 2,   'Euler'], # scapula_de
                [JOINT_LEFT_T4_SHOULDER,'zxy', 1,   'Euler'], # scapula_pr
                [JOINT_LEFT_SHOULDER,   'zxy', 2,   'Euler'], # shoulder_fe
                [JOINT_LEFT_SHOULDER,  'zxy', 0,   'Euler'], # shoulder_aa
                [JOINT_LEFT_SHOULDER,   'zxy', 1,   'Euler'], # shoulder_ie
                [JOINT_LEFT_ELBOW,      'zxy', 2,   'Euler'], # elbow_fe
                [JOINT_LEFT_ELBOW,      'zxy', 1,   'Euler'], # elbow_ps
                [JOINT_LEFT_WRIST,      'zxy', 2,   'Euler'], # wrist_fe
                [JOINT_LEFT_WRIST,      'zxy', 0,   'Euler']] # wrist_dev


    def get_mapped_angle(mvnx, angle_mapping):
        if len(angle_mapping)!=4:
            raise Exception('wrong joint mapping format')
        if (angle_mapping[3] == 'Euler'):
            if(angle_mapping[1]=='xzy'):
                return np.array(mvnx.get_joint_angle_xzy(angle_mapping[0]))[:,angle_mapping[2]]
            if(angle_mapping[1]=='zxy'):
                return np.array(mvnx.get_joint_angle(angle_mapping[0]))[:,angle_mapping[2]]
        elif (angle_mapping[3] == 'Ergo'):
            return np.array(mvnx.get_ergo_joint_angle(angle_mapping[0]))[:,angle_mapping[2]]
        raise Exception('wrong joint mapping format:', angle_mapping[1])

    q = np.array([get_mapped_angle(mvnx_file, x) for x in j_map]) #list of joint angles
    q = q.transpose()

    dt = 1/mvnx_file.frame_rate
    t = np.linspace(0, mvnx_file.frame_count*dt, mvnx_file.frame_count) #assuming frame rate is constant as no direct access to 'ms' value

    return q,dt,t
