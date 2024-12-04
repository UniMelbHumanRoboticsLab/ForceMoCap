# -*- coding: utf-8 -*-
"""
Created on Fri May  3 17:36:59 2024

Set of functions to load, plot and write OpenSIM data (mvt, ID, CMC...) of the
MoBL-ARMS model

@author: vcrocher - Unimelb
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def findHeader(filename: str) -> int:
    '''Find header length of an OpenSIM file. Varies between 5 and 6
    depending on version'''
    with open(filename) as file:
        n=0
        for line in file:
            n+=1
            if(line.rstrip()=='endheader'):
                return n
            if(n>20):
                return 0


## Loading functions

def LoadID(filename: str, name: str = '') -> pd.DataFrame:
    ''' Load an Inverse Dynamic result file'''
    data = pd.read_csv(filename, on_bad_lines='warn', header=findHeader(filename), sep='\s*\t\s*', engine='python', index_col='time')
    data.name=name

    return data


def LoadKin(filename: str, name: str = '') -> pd.DataFrame:
    ''' Load an Inverse Kinematic result file'''
    data = pd.read_csv(filename, on_bad_lines='warn', header=findHeader(filename), sep='\s*\t\s*', engine='python', index_col='time')
    data.name=name

    return data


def LoadCMC(base_filename: str, name: str = '') -> pd.DataFrame:
    ''' Load a CMC result file. TODO.'''
    #States (i.e. everything?)
    filename=base_filename+'_states'+'.sto'

    #Controls (i.e. activations)
    filename=base_filename+'_controls'+'.sto'

    #Actuators
    filename=base_filename+'_Actuation_force'+'.sto'

    data = pd.read_csv(filename, on_bad_lines='warn', header=6, sep='\s*\t\s*', engine='python', index_col='time')

    #Speeds
    filename=base_filename+'_Actuation_speed'+'.sto'

    data.name=name

    return data


## Plotting functions

def PlotIKID(ik_data: pd.DataFrame, id_data: pd.DataFrame, joints: list[str] = []):
    ''' Stack plots of IK data series and one ID data series for specified joints'''
    fig, ax = plt.subplots(2, sharex=True)
    #IK plot
    ik_data.plot(y=joints, ax=ax[0], ylabel='Angle', xlabel='t (s)')
    #ID plot
    for i, j in enumerate(joints):
        joints[i]=j+'_moment'
    id_data.plot(y=joints, ax=ax[1], ylabel='Torque', xlabel='t (s)')

    ax[1].set_title(id_data.name)

    plt.show(block=False)
    for ax in fig.get_axes():
        ax.label_outer()


def PlotCompareIDs(ik_data: pd.DataFrame, id_data: list[pd.DataFrame], joints: list[str] = []):
    ''' Stack plots of one IK data series and multiple ID data series for specified joints'''
    fig, ax = plt.subplots(1+len(joints), sharex=True)
    #IK plot
    ik_data.plot(y=joints, ax=ax[0], ylabel='Angle', xlabel='t (s)')
    #ID plot
    for i, j in enumerate(joints):
        joints[i]=j+'_moment' #same joints but moment value
    styles=['-', ':', '-.', '--', '-', ':']
    #markers=[',', '+', ',', '+', ',', '+']
    markers=[',', ',', ',', ',', ',', ',']
    for n, joint in enumerate(joints):
        legend=[]
        for i, id in enumerate(id_data):
            id_data[i].plot(y=joint, ax=ax[n+1], ylabel='Torque', xlabel='t (s)', linestyle=styles[i], marker=markers[i])
            try:
                legend=legend+[id_data[i].name+' '+joint]
            except AttributeError:
                legend=legend+[joint]
        plt.legend(legend)
        plt.gca().set_prop_cycle(None)

    plt.show(block=False)
    for ax in fig.get_axes():
        ax.label_outer()


def PlotCompareNetMomentIDs(ik_data: pd.DataFrame, id_data: list[pd.DataFrame], joints: list[str] = []):
    ''' Stack plots of IK data series and net moments (absolute value) of ID data series
    for specified joints'''
    fig, ax = plt.subplots(1+len(joints), sharex=True)
    #IK plot
    ik_data.plot(y=joints, ax=ax[0], ylabel='Angle', xlabel='t (s)')
    #ID plot
    for i, j in enumerate(joints):
        joints[i]=j+'_moment' #same joints but moment value
    styles=['-', ':', '-.', '--', '-', ':']
    #markers=[',', '+', ',', '+', ',', '+']
    markers=[',', ',', ',', ',', ',', ',']
    for n, joint in enumerate(joints):
        legend=[]
        for i, id in enumerate(id_data):
            id_data[i][joint]=id_data[i][joint].abs()
            id_data[i].plot(y=joint, ax=ax[n+1], ylabel='Torque', xlabel='t (s)', linestyle=styles[i], marker=markers[i])
            try:
                legend=legend+[id_data[i].name+' '+joint]
            except AttributeError:
                legend=legend+[joint]
        plt.legend(legend)
        plt.gca().set_prop_cycle(None)

    plt.show(block=False)
    for ax in fig.get_axes():
        ax.label_outer()


## Writting functions
#Create OpenSIM files
def WriteOpenSIMKinFile(prefix_filename: str, t: np.array, q: np.array):
    """Write an OpenSIM kinematic file for the MoBL-ARMS model (i.e. output
    of an IK) assuming only joints from the UL 7 DoF model, leaving others to 0
    """
    # Motion file
    motion_filename = prefix_filename + "JointsKin.sto"
    fileD = open(motion_filename, 'w')
    # header
    fileD.write("%s\n" % motion_filename)
    fileD.write("nRows=%d\n" % (q.shape[0] + 1))
    fileD.write("nColumns=%d\n" % 21)  # All these required by MoBL_ARMS model. Most are zero
    fileD.write("inDegrees=no\n")
    fileD.write("endheader\n")
    z = np.zeros((q.shape[0], 1))
    o = np.ones((q.shape[0], 1))
    # MoBL_ARMS requires shoulder1_r2 to be -pi/2 to match...
    fileD.write('time\tsternoclavicular_r2\tsternoclavicular_r3\tunrotscap_r3\tunrotscap_r2\tacromioclavicular_r2\tacromioclavicular_r3\tacromioclavicular_r1\tunrothum_r1\tunrothum_r3\tunrothum_r2\telv_angle\tshoulder_elv\tshoulder1_r2\tshoulder_rot\telbow_flexion\tpro_sup\tdeviation\tflexion\twrist_hand_r1\twrist_hand_r3\n')
    np.savetxt(fileD, np.hstack((t.reshape(-1, 1), np.zeros((q.shape[0], 10)), q[:, 0].reshape(-1, 1), q[:, 1].reshape(-1, 1), -1.57 * o, q[:, 2:8], z, z)), delimiter="\t      ", fmt='%.6f')
    fileD.close()


def WriteOpenSIMForceFile(prefix_filename:str, suffix_filename: str, t: np.array, Force_v: np.array, PtForce_v: np.array):
    """Write an OpenSIM force file for the MoBL-ARMS model (to be use as an
    external force input of an ID, SO or CMC)
    """
    force_filename = prefix_filename + suffix_filename + ".sto"
    fileD = open(force_filename, 'w')
    # header
    fileD.write("%s\n" % force_filename)
    fileD.write("nRows=%d\n" % (Force_v.shape[0] + 1))
    fileD.write("nColumns=7\n")
    fileD.write("inDegrees=no\n")
    fileD.write("endheader\n")
    fileD.write('time\t'+suffix_filename+'_x\t'+suffix_filename+'_y\t'+suffix_filename+'_z\tX_x\tX_y\tX_z\n')
    np.savetxt(fileD, np.hstack((t.reshape(-1, 1), Force_v, PtForce_v)), delimiter='\t      ', fmt='%.6f')
    fileD.close()
