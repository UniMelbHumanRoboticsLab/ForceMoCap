import os, sys,json
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from analysis.analysis_helper import *
from force_tracking.pyqt_vispy.glove_visual_check.hand_process_helper import read_hand_csv, unzip_hand_data_arr

finger_exe_a = [
    {
        "exe_id": "exe1a1.1",
        "wrench_type": ["force", "N"],
    },
    {
        "exe_id": "exe1a1.2",
        "wrench_type": ["force", "N"],
    },
    {
        "exe_id": "exe1a1.3",
        "wrench_type": ["force", "N"],
    },
]
palm_exe_a = [
    {
        "exe_id": "exe1a2.1",
        "wrench_type": ["force", "N"],
    },
    {
        "exe_id": "exe1a2.2",
        "wrench_type": ["force", "N"],
    },
    {
        "exe_id": "exe1a2.3",
        "wrench_type": ["force", "N"],
    }
]

finger_exe_b =[
    {
        "exe_id": "exe1b1.1",
        "wrench_type": ["force", "N"],
    },
    {
        "exe_id": "exe1b1.2",
        "wrench_type": ["force", "N"],
    },
    {
        "exe_id": "exe1b1.3",
        "wrench_type": ["moment", "Nm"],
    },
    {
        "exe_id": "exe1b1.4",
        "wrench_type": ["moment", "Nm"],
    },
    {
        "exe_id": "exe1b1.5",
        "wrench_type": ["moment", "Nm"],
    },
]
full_hand_exe_b = [
    {
        "exe_id": "exe1b2.1",
        "wrench_type": ["force", "N"],
    },
    {
        "exe_id": "exe1b2.2",
        "wrench_type": ["force", "N"],
    },
    {
        "exe_id": "exe1b2.3",
        "wrench_type": ["moment", "Nm"],
    },
    {
        "exe_id": "exe1b2.4",
        "wrench_type": ["moment", "Nm"],
    },
    {
        "exe_id": "exe1b2.5",
        "wrench_type": ["moment", "Nm"],
    },
]

exe_cat_a = {
    "cat_name":"exe_1a",
    "exe_zones":[
        {
            "zone_name":"finger",
            "exercises": finger_exe_a
        },
        {
            "zone_name":"palm",
            "exercises": palm_exe_a
        }
    ]
}
exe_cat_b = {
    "cat_name":"exe_1b", 
    "exe_zones":[
        {
            "zone_name":"finger",
            "exercises": finger_exe_b
        },
        {
            "zone_name":"full_hand",
            "exercises": full_hand_exe_b
        }
    ]
}

exe_categories = [exe_cat_a]

subject_list = [
    {
        "subject_id": "sub1",
        "side": "right",
    }
]

for exe_category in exe_categories:
    for zone in exe_category["exe_zones"]:
        print(f"\nProcessing Exercise: {exe_category['cat_name']}, Zone: {zone['zone_name']}")
        rft_wrenches_df = []
        raw_hand_arr = []

        for subject in subject_list:
            subject_id = subject["subject_id"]
            side = subject["side"]       
            for exe in zone["exercises"]:
                exe_id = exe["exe_id"]
                print(f"Processing {subject_id} {exe_id}")
                for force_level in [5,10,15,20]:
                    cur_sub_exe_level_path = os.path.join(os.path.dirname(__file__),"data",subject_id,exe_id,f"force_{force_level}")
                    cur_rft_wrenches_df = pd.read_csv(os.path.join(cur_sub_exe_level_path, "rft_wrenches.csv"))
                    cur_raw_hand_arr, hand_col, hand_indices = read_hand_csv(cur_sub_exe_level_path,side)

                    rft_wrenches_df.append(cur_rft_wrenches_df)
                    raw_hand_arr.append(cur_raw_hand_arr)

        # start analysis on compiled data for current category and zone
        rft_wrenches_df = pd.concat(rft_wrenches_df).reset_index(drop=True)
        raw_hand_arr = np.vstack(raw_hand_arr)

        phase_1_2_indices = rft_wrenches_df['phase'].isin([1.0, 2.0]).values
        rft_wrenches_df = rft_wrenches_df[phase_1_2_indices].reset_index(drop=True)
        print(f"\nUnzipping Hand Data")
        unzipped_hand_arr,fingers_force_arr,fingers_moment_arr,hand_wrenches_arr = unzip_hand_data_arr(raw_hand_arr[phase_1_2_indices,:], hand_indices)

        # convert hand wrenches to dataframe
        hand_wrenches_df = pd.DataFrame(hand_wrenches_arr, columns=['Fx_hand', 'Fy_hand', 'Fz_hand','Tx_hand', 'Ty_hand', 'Tz_hand'])
        total_wrenches_df = pd.concat([rft_wrenches_df, hand_wrenches_df], axis=1)

        print(f"\nStart Analysis")
        case = f"Exercise: {exe_category['cat_name']}, Zone: {zone['zone_name']}"
        for wrench in ["F","T"]:
            for dim in ["x","y","z"]:
                quantity_rft = f"{wrench}{dim}"
                quantity_hand = f"{wrench}{dim}_hand"
                compare_quantities(total_wrenches_df, quantities=[quantity_rft, quantity_hand], case=f"Wrench_{case}",corr=True)

plt.show()
plt.close('all')
