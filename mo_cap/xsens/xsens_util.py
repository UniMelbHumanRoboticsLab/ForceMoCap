import numpy as np
import struct
import socket
np.set_printoptions(suppress=True, precision=10)

"Function to Start TCP Port for XSENS"
def start_xsens_TCP(timeout):
    TCP_IP = "127.0.0.3"
    TCP_PORT = 9764
    sock = socket.socket(socket.AF_INET, # Internet
                        socket.SOCK_STREAM) # UDP
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow immediate reuse of the port
    sock.bind((TCP_IP, TCP_PORT))
    sock.listen(1)
    conn,addr = sock.accept()
    conn.settimeout(timeout)
    return sock,conn,addr

"""
Base Parse Function
"""
def convert_4_bytes(message:bytes,base_offsets,add_offsets,dtype):
    message_array = np.frombuffer(message, dtype=np.uint8)
    converted_msg = message_array[np.add.outer(base_offsets+add_offsets, np.arange(4))].reshape(-1, 4) # extract the required bytes
    converted_msg = np.frombuffer(converted_msg.tobytes(), dtype=dtype)
    return converted_msg

"""
Parse Functions
"""
def parse_header(message:bytes):
    # refer to MATLAB MVN Streaming example: Deserialize the UDP packet
    message_id = message[0:6].decode('utf-8')
    # sample_count = struct.unpack('>I', message[6:10])[0]+1
    item_number = int(message[11])
    character_id = int(message[16])
    
    # if (message_id == 'MXTP02' and character_id == 1) or \
    # (message_id == 'MXTP25' and character_id == 0) or \
    # (message_id == 'MXTP20' and character_id == 0):
    #     print("==============MessageID:",message_id)
    #     print("character_id:",character_id)
        # print("Datagram_count:",datagram_counter)
        # print("Item Num:",item_number)
        # print("sample count:",sample_count)

    header = {
        'message_id':message_id,
        'character_id':character_id,
    }
    return header

def parse_time(message:bytes):
    return message.decode('utf-8')

def parse_vive_data(message:bytes):
    trackers_num = int(len(message)/32)
    packet_size = 32
    points_list = list(range(trackers_num))
    base_offsets = np.array(points_list) * packet_size
   
    # get the segment id
    ids = convert_4_bytes(message=message,base_offsets=base_offsets,add_offsets=0,dtype='>u4') # '>u4' for big-endian 4-byte unsigned integer
    x_pos = convert_4_bytes(message=message,base_offsets=base_offsets,add_offsets=4,dtype='>f4') # '>f4' for big-endian 4-byte floating point
    y_pos = convert_4_bytes(message=message,base_offsets=base_offsets,add_offsets=8,dtype='>f4') 
    z_pos = convert_4_bytes(message=message,base_offsets=base_offsets,add_offsets=12,dtype='>f4') 
    re = np.rad2deg(convert_4_bytes(message=message,base_offsets=base_offsets,add_offsets=16,dtype='>f4')) # change from rad to degrees like the cpp SDK
    i_comp = np.rad2deg(convert_4_bytes(message=message,base_offsets=base_offsets,add_offsets=20,dtype='>f4') )
    j_comp = np.rad2deg(convert_4_bytes(message=message,base_offsets=base_offsets,add_offsets=24,dtype='>f4'))
    k_comp = np.rad2deg(convert_4_bytes(message=message,base_offsets=base_offsets,add_offsets=28,dtype='>f4') )

    trackers_list = []
    for i in range(trackers_num):
        from scipy.spatial.transform import Rotation as R
        rotation = R.from_quat([i_comp[i],j_comp[i],k_comp[i],re[i]])

        tracker_dict = {
            'id':ids[i],
            'xyz':[x_pos[i],y_pos[i],z_pos[i]],
            'euler-ZYX':rotation.as_euler('ZYX', degrees=True)
        }
        trackers_list.append(tracker_dict)
    return trackers_list
    # ids = np.frombuffer(ids.tobytes(), dtype='>f4')
    # for id in id2:
    #     print(id)

def parse_UL_joint_angle(message: bytes):
    # Compute starting offsets for each joint
    JOINT_RIGHT_T4_SHOULDER = 6
    JOINT_RIGHT_SHOULDER = 7
    JOINT_RIGHT_ELBOW = 8
    JOINT_RIGHT_WRIST = 9
    JOINT_LEFT_T4_SHOULDER = 10
    JOINT_LEFT_SHOULDER = 11
    JOINT_LEFT_ELBOW = 12
    JOINT_LEFT_WRIST = 13
    JOINT_TRUNK = 27

    joints_list = [JOINT_RIGHT_T4_SHOULDER,JOINT_RIGHT_SHOULDER,JOINT_RIGHT_ELBOW,JOINT_RIGHT_WRIST,
                    JOINT_LEFT_T4_SHOULDER,JOINT_LEFT_SHOULDER,JOINT_LEFT_ELBOW,JOINT_LEFT_WRIST,
                    JOINT_TRUNK] # get the order from Analyze Pro
    packet_size = 20
    base_offsets = np.array(joints_list) * packet_size

    x_values = convert_4_bytes(message=message,base_offsets=base_offsets,add_offsets=8,dtype='>f4')
    y_values = convert_4_bytes(message=message,base_offsets=base_offsets,add_offsets=12,dtype='>f4')
    z_values = convert_4_bytes(message=message,base_offsets=base_offsets,add_offsets=16,dtype='>f4')

    # Convert to lists for compatibility
    x_arr = x_values.tolist()
    y_arr = y_values.tolist()
    z_arr = z_values.tolist()

    # extract the joint angles
    JOINT_RIGHT_T4_SHOULDER = 0
    JOINT_RIGHT_SHOULDER = 1
    JOINT_RIGHT_ELBOW = 2
    JOINT_RIGHT_WRIST = 3
    JOINT_LEFT_T4_SHOULDER = 4
    JOINT_LEFT_SHOULDER = 5
    JOINT_LEFT_ELBOW = 6
    JOINT_LEFT_WRIST = 7
    JOINT_TRUNK = 8

    right_joints = {
        'trunk_fe':z_arr[JOINT_TRUNK],
        'trunk_aa':x_arr[JOINT_TRUNK],
        'trunk_ie':y_arr[JOINT_TRUNK],
        'scapula_de':z_arr[JOINT_RIGHT_T4_SHOULDER],
        'scapula_pr':y_arr[JOINT_RIGHT_T4_SHOULDER],
        'shoulder_fe':z_arr[JOINT_RIGHT_SHOULDER],
        'shoulder_aa':x_arr[JOINT_RIGHT_SHOULDER],
        'shoulder_ie':y_arr[JOINT_RIGHT_SHOULDER],
        'elbow_fe':z_arr[JOINT_RIGHT_ELBOW],
        'elbow_ps':y_arr[JOINT_RIGHT_ELBOW],
        'wrist_fe':z_arr[JOINT_RIGHT_WRIST],
        'wrist_dev':x_arr[JOINT_RIGHT_WRIST]
    }

    left_joints = {
        'trunk_fe':z_arr[JOINT_TRUNK],
        'trunk_aa':x_arr[JOINT_TRUNK],
        'trunk_ie':y_arr[JOINT_TRUNK],
        'scapula_de':z_arr[JOINT_LEFT_T4_SHOULDER],
        'scapula_pr':y_arr[JOINT_LEFT_T4_SHOULDER],
        'shoulder_fe':z_arr[JOINT_LEFT_SHOULDER],
        'shoulder_aa':x_arr[JOINT_LEFT_SHOULDER],
        'shoulder_ie':y_arr[JOINT_LEFT_SHOULDER],
        'elbow_fe':z_arr[JOINT_LEFT_ELBOW],
        'elbow_ps':y_arr[JOINT_LEFT_ELBOW],
        'wrist_fe':z_arr[JOINT_LEFT_WRIST],
        'wrist_dev':x_arr[JOINT_LEFT_WRIST]
    }
    return right_joints,left_joints
