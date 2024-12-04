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

import sys,os
sys.path.append(os.path.join(os.path.dirname(__file__)))
from ISBUL import *

class arm_lfd():
    def __init__(self, arm_model_params_d={'torso':0.5,'clav':0.2,'ua_l': 0.3, 'fa_l': 0.25, 'ha_l': 0.1, 'm_ua': 2.0, 'm_fa':1.1+0.23+0.6},model='xsens',arm_side=True):

        self.model = model
        #Handle simple initialisation with overall bidy mass instead of hand, FA and UA masses
        # if 'm_body' in arm_model_params_d:
        #     #7 Dof arm model without masses
        #     self.UL = isb_ul_10dof(arm_model_params_d['ua_l'],
        #                                 arm_model_params_d['fa_l'],
        #                                 arm_model_params_d['ha_l'])
        #     #set masses from body mass
        #     self.ArmMassFromBodyMass(arm_model_params_d['m_body'])
        # #Or init with individual segment masses:
        # else:
        if self.model == 'xsens':
            self.UL = xsens_ul_12dof(arm_model_params_d['torso'],
                                     arm_model_params_d['clav'],
                                     arm_model_params_d['ua_l'],
                                     arm_model_params_d['fa_l'],
                                     arm_model_params_d['ha_l'],
                                     arm_model_params_d['m_ua'],
                                     arm_model_params_d['m_fa'],
                                     arm_side=arm_side)

        # dominant hand
        self.cur_side = arm_side
        
        #Overall arm mass
        self.Marm=0
        for l in self.UL.links:
            self.Marm+=l.m

        #Default gravity vector (can be changed)
        self.UL.gravity=[0,0,-9.81]

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
