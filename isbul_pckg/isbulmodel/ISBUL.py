# -*- coding: utf-8 -*-
"""
Created on Thu May  2 18:22:41 2024

Functionalities using the Robotics toolbox to define an ISb compatible
upper-limb model as a serial manipulator. Same joint angles representation as
the OpenSIM MoBL-ARMS model (https://simtk.org/projects/upexdyn).

@author: vcrocher - Unimelb
"""
import numpy as np
from spatialmath import SO3, SE3
import roboticstoolbox as rtb
#convenience function returning unit vector from a to b
def unit(from_a, to_b):
    return (to_b-from_a)/np.linalg.norm(to_b-from_a)
#convenience function returning unit vector of vec
def unitV(vec):
    return vec/np.linalg.norm(vec)

############### All Available Upper Limb Models ##############################
def xsens_ul_12dof(torso:float,clav:float,ua_l: float, fa_l: float, ha_l: float, m_ua: float = 0, m_fa: float = 0,arm_side:str = "right") -> rtb.Robot:
    """
    xsensUL12DOF Create a Robot of robotic toolbox Xsens compatible arm w/ shoulder elbow and wrist
    ua_l: upper-arm length
    fa_l: forearm length
    ha_l: hand length
    m_ua and m_fa: upper-arm and forearm masses, centered in middle of segment
    - internal/external rotation are not following ISBUL standard for rehabilitation application
    """

    if arm_side == "right":
        L = [] #Links list
        # ROM: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7549223/#:~:text=Normal%20range%20of%20active%20movement,for%20external%20rotation%20%5B6%5D.
        L.append(rtb.RevoluteMDH(d=0,a=0,alpha=0,offset=np.pi/2,name='trunk_ie'))
        L.append(rtb.RevoluteMDH(d=0,a=0,alpha=np.pi/2,offset=np.pi/2,name='trunk_aa'))
        L.append(rtb.RevoluteMDH(d=0,a=0,alpha=np.pi/2,offset=0,name='trunk_fe'))
        L.append(rtb.RevoluteMDH(d=0,a=torso,alpha=np.pi/2,offset=np.pi/2,name='scapula_de'))
        L.append(rtb.RevoluteMDH(d=0,a=0,alpha=np.pi/2,offset=-np.pi/2,name='scapula_pr'))
        L.append(rtb.RevoluteMDH(d=clav,a=0,alpha=np.pi/2,offset=-np.pi/2,name='shoulder_fe'))
        L.append(rtb.RevoluteMDH(d=0,a=0,alpha=np.pi/2,offset=-np.pi/2,name='shoulder_aa'))
        L.append(rtb.RevoluteMDH(d=-ua_l,a=0,alpha=np.pi/2,offset=-np.pi/2,name='shoulder_ie'))
        L.append(rtb.RevoluteMDH(d=0,a=0,alpha=np.pi/2,offset=np.pi,name='elbow_fe'))
        L.append(rtb.RevoluteMDH(d=-fa_l,a=0,alpha=np.pi/2,offset=np.pi,name='elbow_ps'))
        L.append(rtb.RevoluteMDH(d=0,a=0,alpha=np.pi/2,offset=np.pi/2,name='wrist_fe'))
        L.append(rtb.RevoluteMDH(d=0,a=0,alpha=np.pi/2,offset=np.pi/2,name='wrist_dev'))

        xsens = rtb.DHRobot(L)

        #Add hand transformation (tool) to match OpenSIM model wrist offset
        xsens.base=SE3(SO3.Rz(np.pi/2))
        xsens.tool=SE3(SO3.Ry(0))*SE3(SO3.Rx(0))*SE3([0,ha_l,0]) # for intrinsic rotation (rotation about local axis), always use post multiply
    elif arm_side == "left":
        L = [] #Links list
        # ROM: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7549223/#:~:text=Normal%20range%20of%20active%20movement,for%20external%20rotation%20%5B6%5D.
        L.append(rtb.RevoluteMDH(d=0,a=0,alpha=0,offset=np.pi/2,name='trunk_ie'))
        L.append(rtb.RevoluteMDH(d=0,a=0,alpha=np.pi/2,offset=np.pi/2,name='trunk_aa'))
        L.append(rtb.RevoluteMDH(d=0,a=0,alpha=np.pi/2,offset=np.pi,name='trunk_fe'))
        L.append(rtb.RevoluteMDH(d=0,a=-torso,alpha=np.pi/2,offset=np.pi/2,name='scapula_de'))
        L.append(rtb.RevoluteMDH(d=0,a=0,alpha=np.pi/2,offset=-np.pi/2,name='scapula_pr'))
        L.append(rtb.RevoluteMDH(d=-clav,a=0,alpha=np.pi/2,offset=-np.pi/2,name='shoulder_fe'))
        L.append(rtb.RevoluteMDH(d=0,a=0,alpha=np.pi/2,offset=-np.pi/2,name='shoulder_aa'))
        L.append(rtb.RevoluteMDH(d=ua_l,a=0,alpha=np.pi/2,offset=-np.pi/2,name='shoulder_ie'))
        L.append(rtb.RevoluteMDH(d=0,a=0,alpha=np.pi/2,offset=np.pi,name='elbow_fe'))
        L.append(rtb.RevoluteMDH(d=fa_l,a=0,alpha=np.pi/2,offset=np.pi,name='elbow_ps'))
        L.append(rtb.RevoluteMDH(d=0,a=0,alpha=np.pi/2,offset=np.pi/2,name='wrist_fe'))
        L.append(rtb.RevoluteMDH(d=0,a=0,alpha=np.pi/2,offset=-np.pi/2,name='wrist_dev'))

        xsens = rtb.DHRobot(L)

        # #Add hand transformation (tool) to match OpenSIM model wrist offset
        xsens.base=SE3(SO3.Rz(np.pi/2))
        xsens.tool=SE3(SO3.Ry(np.pi))*SE3(SO3.Rx(0))*SE3([0,ha_l,0]) # for intrinsic rotation (rotation about local axis), always use post multiply
    return xsens

def vive_ul_5dof(ua_l: float, fa_l: float, ha_l: float, m_ua: float = 0, m_fa: float = 0,arm_side: str="right") -> rtb.Robot:
    """
    ISB7DOFUL Create a Robot of robotic toolbox engineering compatible arm w/ shoulder elbow and wrist
    ua_l: upper-arm length
    fa_l: forearm length
    ha_l: hand length
    m_ua and m_fa: upper-arm and forearm masses, centered in middle of segment
    right_dom: dominant hand is left or right
    # singularity occurs when elevation is zero, lose a degree of freesom
    """
    if arm_side == "right":
        L = [] #Links list
        # ROM: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7549223/#:~:text=Normal%20range%20of%20active%20movement,for%20external%20rotation%20%5B6%5D.
        L.append(rtb.RevoluteMDH(d=0,       a=0.0,  alpha=np.pi/2,  offset=-np.pi/2, qlim=[-90/180*np.pi, 90/180*np.pi],                                  name='shoulder_fe')) # shoulder flex/extend
        L.append(rtb.RevoluteMDH(d=0,       a=0.0,  alpha=np.pi/2,  offset=np.pi/2,  qlim=[-45/180*np.pi, 135/180*np.pi],                                  name='shoulder_aa')) # shoulder abduct/adduct
        L.append(rtb.RevoluteMDH(d=-ua_l,   a=0.0,  alpha=-np.pi/2, offset=np.pi/2,  qlim=[-90/180*np.pi, 105/180*np.pi],                                  name='shoulder_ie')) # upper arm/shoulder Int/ext
        L.append(rtb.RevoluteMDH(d=0,       a=0,    alpha=np.pi/2,  offset=-np.pi/2, qlim=[-90/180*np.pi, 105/180*np.pi],                                  name='elbow_fe')) # Elbow flex
        L.append(rtb.RevoluteMDH(d=-fa_l,   a=0.0,  alpha=np.pi/2,  offset=-np.pi/2, qlim=[-90/180*np.pi, 120/180*np.pi],     m = m_fa, r = [0,0,-fa_l/2], name='elbow_ps')) # Pronosupination

        ISBUL = rtb.DHRobot(L)

        #Add hand transformation (tool) to match OpenSIM model wrist offset
        #frame: z -> x, x -> -y, y -> -z
        ISBUL.base=SE3(SO3.Rz(np.pi/2))
        ISBUL.tool=SE3(SO3.Rx(np.pi/2))*SE3(SO3.Rz(-np.pi))*SE3([0,ha_l,0])
        # ISBUL.tool=SE3([0,ha_l,0])
    elif arm_side == "left":
        L = [] #Links list
        # ROM: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7549223/#:~:text=Normal%20range%20of%20active%20movement,for%20external%20rotation%20%5B6%5D.
        L.append(rtb.RevoluteMDH(d=0,       a=0.0,  alpha=np.pi/2,  offset=np.pi/2, qlim=[-90/180*np.pi, 90/180*np.pi],                                  name='shoulder_fe')) # shoulder flex/extend
        L.append(rtb.RevoluteMDH(d=0,       a=0.0,  alpha=np.pi/2,  offset=-np.pi/2,  qlim=[-45/180*np.pi, 135/180*np.pi],                                  name='shoulder_aa')) # shoulder abduct/adduct
        L.append(rtb.RevoluteMDH(d=ua_l,    a=0.0,  alpha=np.pi/2,  offset=-np.pi/2,  qlim=[-90/180*np.pi, 105/180*np.pi],                                  name='shoulder_ie')) # upper arm/shoulder Int/ext
        L.append(rtb.RevoluteMDH(d=0,       a=0,    alpha=np.pi/2,  offset=-np.pi/2, qlim=[-90/180*np.pi, 105/180*np.pi],                                  name='elbow_fe')) # Elbow flex
        L.append(rtb.RevoluteMDH(d=fa_l,    a=0.0,  alpha=np.pi/2,  offset=-np.pi/2, qlim=[-90/180*np.pi, 120/180*np.pi],     m = m_fa, r = [0,0,-fa_l/2], name='elbow_ps')) # Pronosupination

        ISBUL = rtb.DHRobot(L)

        #Add hand transformation (tool) to match OpenSIM model wrist offset
        #frame: z -> x, x -> -y, y -> -z
        ISBUL.base=SE3(SO3.Rz(np.pi/2))
        ISBUL.tool=SE3([0,ha_l,0])
        ISBUL.tool=SE3(SO3.Rx(-np.pi/2))*SE3(SO3.Rz(-np.pi))*SE3([0,ha_l,0])
    return ISBUL