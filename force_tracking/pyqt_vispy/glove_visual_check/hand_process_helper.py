import pandas as pd
import numpy as np
from tqdm import tqdm

def read_hand_csv(path,side):
    hand = pd.read_csv(f"{path}/{side}_hand.csv").to_numpy()[:,2:]
    hand_col_head = pd.read_csv(f"{path}/{side}_hand.csv").columns.to_numpy()[2:]
    hand_indices = {}
    for spots in ["thumb","index","middle","ring","pinky","palm_0","palm_1","palm_2","palm_3"]:
        finger_indices = [i for i, s in enumerate(hand_col_head) if spots.lower() in s.lower()]
        hand_indices[spots] = finger_indices
    return hand, hand_col_head, hand_indices

def unzip_hand_data_sample(hand_data,hand_indices):
    # process hand data
    global_t_vecs = []
    global_quat_vecs = []
    force_vecs = []
    moment_vecs = []
    for spots in ["thumb","index","middle","ring","pinky","palm_0","palm_1","palm_2","palm_3"]:
        # print(f"{spots}: {self.left_hand_col[self.left_hand_indices[spots]]}")
        data = hand_data[hand_indices[spots]]
        global_t_vecs.append(data[:3])
        global_quat_vecs.append(data[3:7])
        force_vecs.append(data[7:])
        moment_cur_finger = np.cross(data[:3], data[7:])
        moment_vecs.append(moment_cur_finger)

    hand_data_processed = {
        "global_t_vecs": np.array(global_t_vecs),
        "global_quat_vecs": np.array(global_quat_vecs),
        "force_vecs": np.array(force_vecs),
        "moment_vecs": np.array(moment_vecs)
    }
    return hand_data_processed

def unzip_hand_data_arr(hand_data_arr,hand_indices):
    unzipped_hand_arr = []
    fingers_force_arr = []
    fingers_moment_arr = []
    total_force_arr = []
    total_moment_arr = []
    for raw_hand in tqdm(hand_data_arr):
        hand_data = unzip_hand_data_sample(raw_hand,hand_indices) 
        unzipped_hand_arr.append(hand_data)
        fingers_force_arr.append(hand_data["force_vecs"])
        fingers_moment_arr.append(hand_data["moment_vecs"])
        total_force_arr.append(np.sum(hand_data["force_vecs"], axis=0))
        total_moment_arr.append(np.sum(hand_data["moment_vecs"], axis=0))

    hand_wrenches_arr = np.hstack((np.array(total_force_arr), np.array(total_moment_arr)))
    return unzipped_hand_arr, fingers_force_arr, fingers_moment_arr, hand_wrenches_arr