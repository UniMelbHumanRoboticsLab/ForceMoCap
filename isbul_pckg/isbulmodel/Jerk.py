# -*- coding: utf-8 -*-
"""
Created on Thu May  2 19:37:28 2024

Min jerk trajectory functions

@author: vcrocher - Unimelb
"""
import numpy as np

def Jerk(nbre_pts: int, tf: float, P0: np.array, Pf: np.array, plot=False):
    t=np.linspace(0, tf, nbre_pts)
    to=t/tf
    X = np.empty([3,nbre_pts])
    dX = np.empty([3,nbre_pts])
    ddX = np.empty([3,nbre_pts])
    for i, tto, tt in zip(range(0, nbre_pts), to, t):
        X[:,i]=P0+(P0-Pf)*(15*tto**4 -6*tto**5 -10*tto**3)
        dX[:,i]=(P0-Pf)*(4*15*tto**4/tt -5*6*tto**5/tt -3*10*tto**3/tt)
        ddX[:,i]=(P0-Pf)*(4*3*15*tto**4/(tt**2) -5*4*6*tto**5/(tt**2) -3*2*10*tto**3/(tt**2))
    dX[:,0]=[0,0,0]; #dX(t=0) is undefined, should be 0
    ddX[:,0]=[0,0,0]; #ddX(t=0) is undefined, should be 0

    if(plot):
        import matplotlib.pyplot as plt
        ax=plt.figure().add_subplot(projection='3d')
        ax.plot(X[0,:], X[1,:], X[2,:])
        plt.figure()
        plt.show()
        # plot(t, dX)

    return t, X, dX, ddX
