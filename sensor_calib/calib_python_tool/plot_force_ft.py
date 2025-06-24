import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# configure current sensor parameters
PORT_RFT = "COM7"
PORT_ESP = "COM8"
hand = "left"
sensor = "f1" 
# Finger - f1-thumb,f2-index,f3-middle,f4-ring 
# Palm - p1,p2,p3,p4
angle_config1 = "60"

def analyze_force(force_df:pd.DataFrame):
    fig, (ax1, ax2,ax3) = plt.subplots(3, 1, figsize=(10, 6), sharex=True)

    """plot force-torque-magnet field time series"""
    # First subplot
    ax1.plot(force_df['t'], force_df['Fx'], label='Fx', c = "r")
    ax1.plot(force_df['t'], force_df['Fy'], label='Fy', c = "g")
    ax1.plot(force_df['t'], force_df['Fz'], label='Fz', c = "b")
    ax1.set_title('RFT Force')
    ax1.set_ylabel('F (N)')
    ax1.legend()
    ax1.grid(True)

    # Second subplot
    ax2.plot(force_df['t'], force_df['Tx'], label='Tx',c = "r")
    ax2.plot(force_df['t'], force_df['Ty'], label='Ty',c = "g")
    ax2.plot(force_df['t'], force_df['Tz'], label='Tz',c = "b")
    ax2.set_title('RFT Torque')
    ax2.set_ylabel('tau (Nm)')
    ax2.legend()
    ax2.grid(True)

    # Thirs subplot
    ax3.plot(force_df['t'], force_df['Bx'], label='Bx',c = "r")
    ax3.plot(force_df['t'], force_df['By'], label='By',c = "g")
    ax3.plot(force_df['t'], force_df['Bz'], label='Bz',c = "b")
    ax3.set_title('MLX90393')
    ax3.set_ylabel('Magnetic Field (mT)')
    ax3.set_xlabel('t (s)')
    ax3.legend()
    ax3.grid(True)

    """plot force-magnet field scatter"""
    fig2, (ax1_2, ax2_2, ax3_2) = plt.subplots(1, 3, figsize=(10, 6), sharex=True)

    ax1_2.scatter(force_df['Bx'], force_df['Fx'], label='Fx',c = "r")
    ax1_2.set_title('RFT Force - MLX90393 - X')
    ax1_2.set_ylabel('Force (N)')
    ax1_2.legend()
    ax1_2.grid(True)

    ax2_2.scatter(force_df['By'], force_df['Fy'], label='Fy',c = "g")
    ax2_2.set_title('RFT Force - MLX90393 - Y')
    ax2_2.set_xlabel('Magnetic Field (mT)')
    ax2_2.legend()
    ax2_2.grid(True)

    ax3_2.scatter(force_df['Bz'], force_df['Fz'], label='Fz',c = "b")
    ax3_2.set_title('RFT Force - MLX90393 - Z')
    ax3_2.legend()
    ax3_2.grid(True)

    """plot torque-magnet field scatter"""
    fig3, (ax1_3, ax2_3, ax3_3) = plt.subplots(1, 3, figsize=(10, 6), sharex=True)

    ax1_3.scatter(force_df['Bx'], force_df['Tx'], label='Tx',c = "r")
    ax1_3.set_title('RFT Torque - MLX90393 - X')
    ax1_3.set_ylabel('Torque (Nm)')
    ax1_3.legend()
    ax1_3.grid(True)

    ax2_3.scatter(force_df['By'], force_df['Ty'], label='Ty',c = "g")
    ax2_3.set_title('RFT Torque - MLX90393 - Y')
    ax2_3.set_xlabel('Magnetic Field (mT)')
    ax2_3.legend()
    ax2_3.grid(True)

    ax3_3.scatter(force_df['Bz'], force_df['Tz'], label='Tz',c = "b")
    ax3_3.set_title('RFT Torque - MLX90393 - Z')
    ax3_3.legend()
    ax3_3.grid(True)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    for i in [0,15,30]:
        force_df = pd.read_csv(f"sensor_calib/data/{hand}/{sensor}/force_{angle_config1}_{i}.csv")
        analyze_force(force_df=force_df)
