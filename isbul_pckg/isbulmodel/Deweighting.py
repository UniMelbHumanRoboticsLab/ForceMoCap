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

from .ISBUL import *


class Deweighting():

    def __init__(self, arm_model_params_d={'ua_l': 0.3, 'fa_l': 0.25, 'ha_l': 0.1, 'm_ua': 2.0, 'm_fa':1.1+0.23+0.6}):

        #Handle simple initialisation with overall bidy mass instead of hand, FA and UA masses
        if 'm_body' in arm_model_params_d:
            #7 Dof arm model without masses
            self.UL = ISB_7DOF_UL(arm_model_params_d['ua_l'],
                                    arm_model_params_d['fa_l'],
                                    arm_model_params_d['ha_l'])
            #set masses from body mass
            self.ArmMassFromBodyMass(arm_model_params_d['m_body'])
        #Or init with individual segment masses:
        else:
            #7 Dof arm model
            self.UL = ISB_7DOF_UL(arm_model_params_d['ua_l'],
                                    arm_model_params_d['fa_l'],
                                    arm_model_params_d['ha_l'],
                                    arm_model_params_d['m_ua'],
                                    arm_model_params_d['m_fa'])

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



    def DeweightForce(self, q: np.array) -> np.array:
        ''' Compute end-effector (hand) equivalent deweigting force based on
        model parameters and arm posture q'''
        #Ensure q array is correct, otherwise 0 force
        if(np.isnan(q).sum()>0):
            return np.array([0,0,0])

        #Singularity (full ext) check and avoidance to avoid large forces:
        eps = np.pi/5
        if(abs(q[1]-np.pi/2)+abs(q[3])<eps):
            #q[1] = ??
            #q[3] = ??
            print('EMUDeweightForce at singularity (', q, '): setting posture at ', q)

        #Gravitational torques
        taug = self.UL.gravload(q)

        #Compute deweight force
        J = self.UL.jacob0(q, half='trans')
        Jt = J.transpose()
        F = Jt.dot(np.linalg.inv(J.dot(Jt))).transpose().dot(taug) # Right Moore-Penrose pseudo inverse transpose times tau

        return F

    def DynamicDeweightForce(self, q: np.array, ddX: np.array, eps: float=0.05) -> np.array:
        ''' Deweigting force based on model parameters and arm posture q (EMUDeweightForce)
        and hand acceleration provided: deweighting off for negative Z acceleration'''
        #Simple on/off based on acceleration: no smooth transition here
        if(ddX[2]<-eps):
            return np.zeros((3))
        else:
            return self.DeweightForce(q)

    def VelocityBasedDeweightForce(self, q: np.array, dX: np.array, eps: float=0.1) -> np.array:
        ''' Deweigting force based on model parameters and arm posture q (EMUDeweightForce)
        and hand velocity provided: deweighting off for downwards movements'''
        #Which movement direction? No smooth transition here: pure on/off
        if(dX[2]<-eps):#m.s-1
            return np.zeros((3))
        else:
            return self.DeweightForce(q)

    def CstDeweightForce(self, weight_portion: float=1.0) -> np.array:
        '''Constant deweighting force vector as portion of overall arm mass'''
        return -self.UL.gravity*self.Marm*weight_portion
