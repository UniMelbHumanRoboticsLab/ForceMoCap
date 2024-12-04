# -*- coding: utf-8 -*-
"""
Load a set of kinematic recordings from the ULF_ADL dataset and convert them to
a 7DoF arm model (isbulm) and save them as a single panda dataframe in a pickle
file.

14/11/2024

@author: vcrocher
"""
import numpy as np

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from isbul_pckg.isbulmodel.arm_lfd import arm_lfd
from mo_cap.xsens.mvnx_util import convert_mvn_to_isb_angles

def adl_ul_convert(base_dir, output_dir, to_load, plot=False):
    #Build relative filename to load
    base_filename= ''
    if to_load['type']=='H' :
        base_filename = to_load['type'] + to_load['id'] + '_T' + to_load['task'] + '_' + to_load['side'] + str(to_load['rep'])
        file_name = base_dir + 'Healthies/' \
        + to_load['type'] + to_load['id'] + '_SoftProTasks/' \
        + base_filename \
        + '.mvnx'
    else:
        base_filename = to_load['type'] + to_load['id'] + '_T' + to_load['task'] + '_' + to_load['side'] + str(to_load['rep'])
        file_name = base_dir + 'Strokes/' \
        + to_load['type'] + to_load['id'] + '_SoftProTasks/' \
        + base_filename \
        + '.mvnx'

    # Check for file existence
    if not os.path.isfile(file_name):
        raise Exception("File %s could not be found" % file_name)

    print("--- Processing ", file_name)

    if to_load['side'] == 'R':
        side = "right"
    else:
        side = "left"
    
    q,dt,t = convert_mvn_to_isb_angles(file_name,side)

    arm_model_params_d = {'torso':0.6,
            'clav': 0.2,
            'ua_l': 0.3,
            'fa_l': 0.25,
            'ha_l': 0.05,
            'm_ua': 2.0,
            'm_fa': 1.1+0.23+0.6}
    ul_model = arm_lfd(arm_model_params_d,model="xsens",arm_side=side)

        # assert 0
    ul_model.UL.plot(np.deg2rad(q[0::5]),block=True,loop=False)

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


#%% Load and convert a number of selected files for relevant tasks
files_dir = './ULF_in_ADL/'
output_dir= './ULF_in_ADL/export/'


tasks_of_interest = ['12']
#Allassumed right-handed as paper does not specifiy
Healthies = [   {'id': '01', 's': 'R'},
                {'id': '02', 's': 'R'},
                {'id': '03', 's': 'R'},
                {'id': '04', 's': 'R'},
                {'id': '05', 's': 'R'}
                ]

#Selected right handed & right impaired to match helathy and get only consistent impaired-dominant
Strokes = [ {'id': '03', 's':'R'},
            {'id': '05', 's':'R'},
            {'id': '12', 's':'R'},
            {'id': '21', 's':'R'},
            {'id': '30', 's':'R'}
            ]

for t in tasks_of_interest:
    for r in [1, 2, 3]:
        for h in Healthies:
            to_load = {'type': 'H', # Healthy
                        'id': h['id'], #subject id: H 01 to 05 and S 02-30 but imcomplete
                        'task': t, #task number 01 - 30
                        'side': h['s'], # 'L' #armside
                        'rep': r# repetition 1-3 (incomplete)
                        }
            adl_ul_convert(files_dir, output_dir, to_load)
        for s in Strokes:
            to_load = {'type': 'P', #Stroke
                        'id': s['id'], #subject id: H 01 to 05 and S 02-30 but imcomplete
                        'task': t, #task number 01 - 30
                        'side': s['s'], # 'L' #armside
                        'rep': r# repetition 1-3 (incomplete)
                        }
            adl_ul_convert(files_dir, output_dir, to_load)


#%% For quick test

# #File to load and convert
# to_load = {'type': 'H', #'S'
#            'id': '04', #subject id: H 01 to 05 and S 02-30 but imcomplete
#            'task': '12', #task number 01 - 30
#            'side': 'L', # 'L' #armside
#            'rep': 2# repetition 1-3 (incomplete)
#            }

# ConvertMVNXRecordingToISBULpickle(files_dir, output_dir, to_load, True)
