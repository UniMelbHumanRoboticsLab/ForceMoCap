import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
from .plot_force_ft import analyze_force

def calib_force(df:pd.DataFrame):
     p = 0
     
if __name__ == "__main__":
    for hand in ["left","right"]:
        for sensor in ["f1","f2","f3","f4","p1","p2","p3","p4"]:
                calib_files = os.listdir(f"sensor_calib/data/{hand}/{sensor}") 
                calib_df = []
                for file in calib_files:
                    cur_force_df = pd.read_csv(f"sensor_calib/data/{hand}/{sensor}/{file}")
                    calib_df.append(cur_force_df)

                calib_df = pd.concat(calib_df)
                analyze_force(calib_df)

                # write the calibration algo here to get a calibration matrix and save the matrix to respective folder
                # is it logical to also map to the torque 
                