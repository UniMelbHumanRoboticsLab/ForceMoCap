import os, sys,json
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from analysis.analysis_helper import *
from force_tracking.pyqt_vispy.glove_visual_check.hand_process_helper import read_hand_csv, unzip_hand_data_arr

subject_name = "JQ"
exe_id = "exe1"
side = "right"
rft_wrenches_df = []
raw_hand_arr = []
for force_level in [10,15]:
    cur_sub_exe_level_path = os.path.join(os.path.dirname(__file__),"data",subject_name,exe_id,f"force_{force_level}")
    cur_rft_wrenches_df = pd.read_csv(os.path.join(cur_sub_exe_level_path, "rft_wrenches.csv"))
    cur_raw_hand_arr, hand_col, hand_indices = read_hand_csv(cur_sub_exe_level_path,side)

    rft_wrenches_df.append(cur_rft_wrenches_df)
    raw_hand_arr.append(cur_raw_hand_arr)
rft_wrenches_df = pd.concat(rft_wrenches_df).reset_index(drop=True)
raw_hand_arr = np.vstack(raw_hand_arr)

phase_1_2_indices = rft_wrenches_df['phase'].isin([1.0, 2.0]).values
rft_wrenches_df = rft_wrenches_df[phase_1_2_indices].reset_index(drop=True)
print("\nUnzip hand data")
unzipped_hand_arr,fingers_force_arr,fingers_moment_arr,hand_wrenches_arr = unzip_hand_data_arr(raw_hand_arr[phase_1_2_indices,:], hand_indices)

# convert hand wrenches to dataframe
hand_wrenches_df = pd.DataFrame(hand_wrenches_arr, columns=['Fx_hand', 'Fy_hand', 'Fz_hand','Tx_hand', 'Ty_hand', 'Tz_hand'])
total_wrenches_df = pd.concat([rft_wrenches_df, hand_wrenches_df], axis=1)

print("\nStart Analysis")
force_level = "total"
for wrench in ["F","T"]:
    for dim in ["x","y","z"]:
        quantity_rft = f"{wrench}{dim}"
        quantity_hand = f"{wrench}{dim}_hand"
        compare_quantities(total_wrenches_df, quantities=[quantity_rft, quantity_hand], case=f"Wrench_{force_level}_{wrench}{dim}",corr=True)

plt.show()
plt.close('all')
p = 0