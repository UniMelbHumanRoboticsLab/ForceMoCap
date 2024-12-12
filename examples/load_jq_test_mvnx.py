# -*- coding: utf-8 -*-
"""
Load a set of kinematic recordings from the ULF_ADL dataset and convert them to
a 12DoF arm model (isbulm) and save them as a single panda dataframe in a pickle
file.

14/11/2024

@author: vcrocher
"""
import numpy as np

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from isbul_pckg.isbulmodel.arm_lfd import arm_lfd
sys.path.append(os.path.join(os.path.dirname(__file__), '..','mo_cap/xsens'))
from mo_cap.xsens.mvnx_util import convert_mvn_to_isb_angles

# Load and convert a selected file
files_dir = './ULF_in_ADL/'
output_dir= './export/'
side = "right"
#Build relative filename to load
file_name = files_dir + 'JQ_Test/' \
    + "mvnx_files/" + 'pure_elbow_flex-001' \
    + '.mvnx'
# Check for file existence
if not os.path.isfile(file_name):
    raise Exception("File %s could not be found" % file_name)

print("--- Processing ", file_name)
q,dt,t = convert_mvn_to_isb_angles(file_name,side)

body_params = {'torso':0.6,
        'clav': 0.2,
        'ua_l': 0.3,
        'fa_l': 0.25,
        'ha_l': 0.05,
        'm_ua': 2.0,
        'm_fa': 1.1+0.23+0.6}
ul_model = arm_lfd(body_params,model="xsens",arm_side=side)

    # assert 0
ul_model.UL.plot(np.deg2rad(q[0::5]),block=True,loop=True)
#Create a panda datframe of the movements with 7DoFs arm format
#the df is intended to hold joint angle sequence and time of a single movement
#and save in a separate into subject/task/repetition files
# mvt = np.vstack((t,q))
# df = pd.DataFrame(mvt.transpose(), columns=['t', 'q0', 'q1', 'q2', 'q3', 'q4', 'q5', 'q6'])
# export_file_name = output_dir+base_filename+'.csv'
# with open(export_file_name, 'wb') as handle:
#     #pickle.dump(df, handle, protocol=pickle.HIGHEST_PROTOCOL)
#     df.to_csv(handle)

# print("saved as ", export_file_name)