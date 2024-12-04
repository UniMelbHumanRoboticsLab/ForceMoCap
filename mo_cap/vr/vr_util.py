from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import pandas as pd
from matplotlib import animation
from spatialmath import SE3,SO3
from scipy.spatial.transform import Rotation as R
import matplotlib.pyplot as plt
import os
import sys
from sksurgerycore.algorithms.averagequaternions import average_quaternions
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from isbul_pckg.isbulmodel.arm_lfd import armLFD
np.set_printoptions(suppress=True,precision=4) # suppress scientific notation

"""
Visualize skeleton (joint position)
"""
def visual_skeleton(x,y,z,top_cam=[0,270,0],side_cam=[0,0,90],axis='z'):
    fig = plt.figure()
    ax = fig.add_subplot(1,2,1,projection='3d')
    ax2 = fig.add_subplot(1,2,2,projection='3d')
    ax.view_init(elev=top_cam[0], azim=top_cam[1],roll=top_cam[2],vertical_axis=axis)
    ax2.view_init(elev=side_cam[0], azim=side_cam[1],roll=side_cam[2],vertical_axis=axis)
    ax.set_box_aspect([1, 1, 1])
    ax2.set_box_aspect([1, 1, 1])

    # top view
    top, = ax.plot(x[0],y[0],z[0],marker='o', linestyle='-', color='b')
    ax.set_xlabel('X1')
    ax.set_xlim(-0.5,1)
    ax.set_ylabel('Y1')
    ax.set_ylim(-0.5,1)
    ax.set_zlabel('Z1')
    ax.set_zlim(-0.5,1)
    ax.set_title("Top")

    # side view
    side, = ax2.plot(x[0],y[0],z[0],marker='o', linestyle='-', color='b')
    ax2.set_xlabel('X2')
    ax2.set_xlim(-0.5,1)
    ax2.set_ylabel('Y2')
    ax2.set_ylim(-0.5,1)
    ax2.set_zlabel('Z2')
    ax2.set_zlim(-0.5,1)
    ax2.set_title("Side")

    def update(num,top,side,invert1,invert2):
        ax.set_box_aspect([1, 1, 1])
        ax2.set_box_aspect([1, 1, 1])
        # again, Unity is dumb, so have to reverse axis thing :)
        if axis =='y':
            invert1.set_inverted(True)
            invert2.set_inverted(True)

        top.set_data(x[num],y[num])
        top.set_3d_properties(z[num])

        side.set_data(x[num],y[num])
        side.set_3d_properties(z[num])

        # tp_side1.set_data(x[num],y[num])
        # tp_side2.set_data(x[num],y[num])
        # tp_side1.set_3d_properties(z[num])
        # tp_side2.set_3d_properties(z[num])

        return top,side

    if axis == 'y':
        ax.invert_zaxis()
        ax2.invert_zaxis()

    ani = animation.FuncAnimation(fig, update, x.shape[0], fargs=(top,side,ax.zaxis,ax2.zaxis), interval=5, blit=True)
    
    plt.show(block=True)
    plt.close('all')
"""
Visualize skeleton (joint position) and task parameters
"""
def visual_skeleton_n_task_params(x,y,z,tp_positions,top_cam=[0,270,0],side_cam=[0,0,90],axis='z'):
    fig = plt.figure()
    fig.suptitle("Visual Raw Skeleton and TP")
    ax = fig.add_subplot(1,2,1,projection='3d')
    ax2 = fig.add_subplot(1,2,2,projection='3d')
    ax.view_init(elev=top_cam[0], azim=top_cam[1],roll=top_cam[2],vertical_axis=axis)
    ax2.view_init(elev=side_cam[0], azim=side_cam[1],roll=side_cam[2],vertical_axis=axis)
    ax.set_box_aspect([1, 1, 1])
    ax2.set_box_aspect([1, 1, 1])

    # top view
    top, = ax.plot(x[0],y[0],z[0],marker='o', linestyle='-', color='b')
    # Initialize scatters
    tp_top, = ax.plot(tp_positions[0,:,0],tp_positions[0,:,1],tp_positions[0,:,2],marker='o', linestyle='None', color='r')
    ax.set_xlabel('X1')
    ax.set_xlim(-0.5,1)
    ax.set_ylabel('Y1')
    ax.set_ylim(-0.5,1)
    ax.set_zlabel('Z1')
    ax.set_zlim(-0.5,1)
    ax.set_title("Top")

    # side view
    side, = ax2.plot(x[0],y[0],z[0],marker='o', linestyle='-', color='b')
    tp_side, = ax2.plot(tp_positions[0,:,0],tp_positions[0,:,1],tp_positions[0,:,2],marker='o', linestyle='None', color='r')
    ax2.set_xlabel('X2')
    ax2.set_xlim(-0.5,1)
    ax2.set_ylabel('Y2')
    ax2.set_ylim(-0.5,1)
    ax2.set_zlabel('Z2')
    ax2.set_zlim(-0.5,1)
    ax2.set_title("Side")

    def update(num,top,side,tp_top,tp_side,invert1,invert2):
        ax.set_box_aspect([1, 1, 1])
        ax2.set_box_aspect([1, 1, 1])
        # again, Unity is dumb, so have to reverse axis thing :)
        if axis =='y':
            invert1.set_inverted(True)
            invert2.set_inverted(True)

        top.set_data(x[num],y[num])
        top.set_3d_properties(z[num])

        side.set_data(x[num],y[num])
        side.set_3d_properties(z[num])

        tp_top.set_data(tp_positions[num,:,0],tp_positions[num,:,1])
        tp_top.set_3d_properties(tp_positions[num,:,2])

        tp_side.set_data(tp_positions[num,:,0],tp_positions[num,:,1])
        tp_side.set_3d_properties(tp_positions[num,:,2])

        # tp_side1.set_data(x[num],y[num])
        # tp_side2.set_data(x[num],y[num])
        # tp_side1.set_3d_properties(z[num])
        # tp_side2.set_3d_properties(z[num])

        return top,side,tp_top,tp_side

    if axis == 'y':
        ax.invert_zaxis()
        ax2.invert_zaxis()

    ani = animation.FuncAnimation(fig, update, x.shape[0], fargs=(top,side,tp_top,tp_side,ax.zaxis,ax2.zaxis), interval=5, blit=True)
    
    plt.show(block=True)
    plt.close('all')

"""
Calculate ua length and forearm length

"""
def calc_body_params(wrist_traj,elbow_traj,shoulder_traj,hand_length):
    upper_arm_lengths = []
    fore_arm_lengths = []
    for wrist,elbow,shoulder in zip(wrist_traj,elbow_traj,shoulder_traj):
        upper_arm_lengths.append(np.linalg.norm(shoulder.t-elbow.t))
        fore_arm_lengths.append(np.linalg.norm(elbow.t-wrist.t))
    upper_arm = np.mean(np.array(upper_arm_lengths))
    fore_arm = np.mean(np.array(fore_arm_lengths))
    body = pd.DataFrame([[0,upper_arm,fore_arm,hand_length]], columns=["shoulder","ua","fa","hand"])
    return body

"""
Convert joint frames from left hand unity frame to right hand robot frame
- calculate bias from the IMU
- change left to right hand 
- adjust joints to joint center and transform everything to shoulder frame, can also visualize marker frame changing
- return a list of SE3 objects representing SE3 at each point in time

"""
def l2rTransform(joint_orient,joint_trans):
    """
    Transform the frames from left hand unity to right hand rbt-toolbox 
    https://www.gamedev.net/forums/topic/607423-convert-left-hand-rotations-to-right-hand/
    FUCK UNITY
    """
    permute = np.array([[1,0,0],[0,0,1],[0,1,0]])
    R_tot = np.matmul(permute.T,np.matmul(joint_orient.as_matrix(),permute))
    t = np.matmul(permute,joint_trans)
    joint_rbt = SE3.Rt(R_tot,t) # adjusted right hand frame
    return joint_rbt
def get_imu_bias(wrist,elbow,shoulder,arm_side,visualize):
    """
    This performs Unity-to-right hand transform and offsets the joints to the joint centre
    Also find the average task parameter position with respect to the shoulder
    """
    shoulder = shoulder.values
    wrist = wrist.values
    elbow = elbow.values

    shoulder_bias = []
    elbow_bias = []
    wrist_bias = []

    for num in range(0,shoulder.shape[0]):

        shoulder_orient = R.from_quat(shoulder[num,3:])
        shoulder_trans = shoulder[num,:3]
        shoulder_UA = l2rTransform(shoulder_orient,shoulder_trans)
        if arm_side == 'right':
            ideal_shoulder = SE3.Rt(np.array([[1,0,0],[0,1,0],[0,0,1]])*SO3.Rx(90,'deg'),shoulder_UA.t) # ideal shoulder
        elif arm_side == "left":
            ideal_shoulder = SE3.Rt(np.array([[1,0,0],[0,1,0],[0,0,1]])*SO3.Rx(90,'deg')*SO3.Ry(180,'deg'),shoulder_UA.t) # ideal shoulder
        bias = (ideal_shoulder.inv()*shoulder_UA).inv() # bias from actual to ideal
        shoulder_transformed = SE3.Rt(np.matmul(shoulder_UA.R,bias.R),shoulder_UA.t) # to rotate actual frame back to ideal frame
        quat = R.from_matrix(bias.R).as_quat()
        shoulder_bias.append(quat)

        elbow_orient = R.from_quat(elbow[num,3:])
        elbow_trans = elbow[num,:3]
        elbow_UA = l2rTransform(elbow_orient,elbow_trans)
        if arm_side == 'right':
            ideal_elbow = SE3.Rt(np.array([[1,0,0],[0,1,0],[0,0,1]])*SO3.Rx(90,'deg'),elbow_UA.t) # ideal elbow
        elif arm_side == "left":
            ideal_elbow = SE3.Rt(np.array([[1,0,0],[0,1,0],[0,0,1]])*SO3.Rx(90,'deg')*SO3.Ry(180,'deg'),elbow_UA.t) # ideal shoulder
        bias = (ideal_elbow.inv()*elbow_UA).inv() # bias from actual to ideal
        elbow_transformed = SE3.Rt(np.matmul(elbow_UA.R,bias.R),elbow_UA.t) # to rotate actual frame to ideal frame
        quat = R.from_matrix(bias.R).as_quat()
        elbow_bias.append(quat)
        
        wrist_orient = R.from_quat(wrist[num,3:])
        wrist_trans = wrist[num,:3]
        wrist_UA = l2rTransform(wrist_orient,wrist_trans)
        ideal_wrist = SE3.Rt(np.array([[1,0,0],[0,1,0],[0,0,1]])*SO3.Rx(90,'deg'),wrist_UA.t) # ideal wrist
        if arm_side == 'right':
            ideal_wrist = SE3.Rt(np.array([[1,0,0],[0,1,0],[0,0,1]])*SO3.Rx(90,'deg'),wrist_UA.t) # ideal elbow
        elif arm_side == "left":
            ideal_wrist = SE3.Rt(np.array([[1,0,0],[0,1,0],[0,0,1]])*SO3.Rx(90,'deg')*SO3.Ry(180,'deg'),wrist_UA.t) # ideal shoulder
        bias = (ideal_wrist.inv()*wrist_UA).inv() # bias from actual  to ideal
        wrist_transformed = SE3.Rt(np.matmul(wrist_UA.R,bias.R),wrist_UA.t) # to rotate actual frame to ideal frame
        quat = R.from_matrix(bias.R).as_quat()
        wrist_bias.append(quat)

    avg_shoulder_bias = average_quaternions(np.array(shoulder_bias))
    avg_elbow_bias = average_quaternions(np.array(elbow_bias))
    avg_wrist_bias = average_quaternions(np.array(wrist_bias))

    if visualize:
        fig = plt.figure()
        ax1 = fig.add_subplot(1,1,1,projection='3d')
        for num in range(0,shoulder.shape[0]):

            shoulder_orient = R.from_quat(shoulder[num,3:])
            shoulder_trans = shoulder[num,:3]
            shoulder_UA = l2rTransform(shoulder_orient,shoulder_trans)
            shoulder_transformed = SE3.Rt(np.matmul(shoulder_UA.R,R.from_quat(avg_shoulder_bias).as_matrix()),shoulder_UA.t) # to rotate actual frame back to ideal frame
            shoulder_UA.plot(frame=f's{num}-u',color='k',length=0.05,ax=ax1)
            shoulder_transformed.plot(frame=f's{num}-t',color='b',length=0.05,ax=ax1)

            elbow_orient = R.from_quat(elbow[num,3:])
            elbow_trans = elbow[num,:3]
            elbow_UA = l2rTransform(elbow_orient,elbow_trans)
            elbow_transformed = SE3.Rt(np.matmul(elbow_UA.R,R.from_quat(avg_elbow_bias).as_matrix()),elbow_UA.t) # to rotate actual frame back to ideal frame
            elbow_UA.plot(frame=f'e{num}-u',color='k',length=0.05,ax=ax1)
            elbow_transformed.plot(frame=f'e{num}-t',color='b',length=0.05,ax=ax1)
            
            wrist_orient = R.from_quat(wrist[num,3:])
            wrist_trans = wrist[num,:3]
            wrist_UA = l2rTransform(wrist_orient,wrist_trans)
            wrist_transformed = SE3.Rt(np.matmul(wrist_UA.R,R.from_quat(avg_wrist_bias).as_matrix()),wrist_UA.t) # to rotate actual frame back to ideal frame
            wrist_UA.plot(frame=f'w{num}-u',color='k',length=0.05,ax=ax1)
            wrist_transformed.plot(frame=f'w{num}-t',color='b',length=0.05,ax=ax1)

            plt.pause(0.3)
            ax1.clear()

    return R.from_quat(avg_shoulder_bias).as_matrix(),R.from_quat(avg_elbow_bias).as_matrix(),R.from_quat(avg_wrist_bias).as_matrix()
def adjust_joints_and_task_points(wrist,elbow,shoulder,shoulder_offset,elbow_offset,wrist_offset,task_points_df,task_points_offset,bias,visualize,loop):

    """
    This performs Unity-to-right hand transform and offsets the joints to the joint centre
    Also find the average task parameter position with respect to the shoulder
    """
    shoulder = shoulder.values
    wrist = wrist.values
    elbow = elbow.values

    task_points = []
    for task_point in task_points_df:
        task_points.append(task_point.values)

    shoulder_UA_traj = []
    shoulder_rbt_traj = []
    shoulder_UA_mid_est_traj = []

    elbow_UA_traj = []
    elbow_UA_mid_est_traj = []

    wrist_UA_traj = []
    wrist_UA_mid_est_traj = []

    task_points_rbt_traj = []
    task_points_UA_traj = []

    for num in range(0,shoulder.shape[0]):
        shoulder_orient = R.from_quat(shoulder[num,3:])
        shoulder_trans = shoulder[num,:3]
        shoulder_UA = l2rTransform(shoulder_orient,shoulder_trans) # uncalibrated shoulder
        ideal = SE3.Rt(np.array([[1,0,0],[0,1,0],[0,0,1]])*SO3.Rx(90,'deg'),shoulder_UA.t)
        shoulder_UA = SE3.Rt(shoulder_UA.R@bias[0],shoulder_UA.t) # calibrated shoulder
        shoulder_offset_world = np.matmul(shoulder_UA.R,np.array(shoulder_offset))
        shoulder_UA_mid_est = SE3.Rt(shoulder_UA.R,shoulder_UA.t+shoulder_offset_world)
        shoulder_rbt = SE3.Rt(ideal.R*SO3.Rx(-90, 'deg'), shoulder_UA.t) # transform the marker from UA frame to robot base frame, post-multiply for local rotation
        
        elbow_orient = R.from_quat(elbow[num,3:])
        elbow_trans = elbow[num,:3]
        elbow_UA = l2rTransform(elbow_orient,elbow_trans)
        elbow_offset_world = np.matmul(elbow_UA.R,np.array(elbow_offset))
        elbow_UA_mid_est = SE3.Rt(elbow_UA.R@bias[1],elbow_UA.t+elbow_offset_world) # calibrated elbow
        elbow_UA = SE3.Rt(elbow_UA.R@bias[1],elbow_UA.t) # transform to ideal sensor frame
        
        wrist_orient = R.from_quat(wrist[num,3:])
        wrist_trans = wrist[num,:3]
        wrist_UA = l2rTransform(wrist_orient,wrist_trans)
        wrist_offset_world = np.matmul(wrist_UA.R,np.array(wrist_offset))
        wrist_UA_mid_est = SE3.Rt(wrist_UA.R@bias[2],wrist_UA.t+wrist_offset_world) # calibrated wrist
        wrist_UA = SE3.Rt(wrist_UA.R@bias[2],wrist_UA.t) # transform to ideal sensor frame

        # collect the transformation matrix for joints in the Upper Arm Frame
        shoulder_UA_traj.append(shoulder_UA)
        shoulder_UA_mid_est_traj.append(shoulder_UA_mid_est)
        shoulder_rbt_traj.append(shoulder_rbt)

        elbow_UA_traj.append(elbow_UA)
        elbow_UA_mid_est_traj.append(elbow_UA_mid_est)

        wrist_UA_traj.append(wrist_UA)
        wrist_UA_mid_est_traj.append(wrist_UA_mid_est)

        # transform the task points relative to the robot base (shoulder_base) as the origin
        task_points_rbt = []
        task_points_UA = [] 
        for item,task_point in enumerate(task_points):
            tp_orient = R.from_quat(task_point[num,3:])
            tp_trans = task_point[num,:3]
            tp_UA = l2rTransform(tp_orient,tp_trans) 
            tp_rbt = shoulder_rbt.inv()*SE3.Trans(tp_UA.t)
            task_points_rbt.append(tp_rbt.t) # collect the task positions
            task_points_UA.append(tp_UA.t)
        task_points_rbt_traj.append(task_points_rbt)
        task_points_UA_traj.append(task_points_UA)
    
    avg_task_points_rbt = np.mean(np.array(task_points_rbt_traj),axis = 0)
    avg_task_points_rbt = avg_task_points_rbt + np.array(task_points_offset)# find the average position of the task parameters in world and offset it to the estimated wrist
    avg_task_points_rbt = [avg_task_points_rbt[0],avg_task_points_rbt[1]]

    avg_task_points_UA = np.mean(np.array(task_points_UA_traj),axis = 0)
    avg_task_points_UA = avg_task_points_UA + np.array(task_points_offset)# find the average position of the task parameters in world and offset it to the estimated wrist
    avg_task_points_UA = [avg_task_points_UA[0],avg_task_points_UA[1]]
    if visualize: # see how frames move
        fig = plt.figure()
        fig.suptitle("Visual Adjusted Skeleton and TP")
        ax2 = fig.add_subplot(1,1,1,projection='3d')
        ax2.view_init(elev=42, azim=-50,vertical_axis='z')
        ax2.set_box_aspect([1, 1, 1])
        ax2.set_xlabel('X2')
        ax2.set_xlim(-0.5,1)
        ax2.set_ylabel('Y2')
        ax2.set_ylim(-0.5,1)
        ax2.set_zlabel('Z2')
        ax2.set_zlim(-0.5,1)
        
        plt.pause(1)
        while(True):
            i = -1
            step = 25 # only plot every 10th trajectry element
            world = SE3.Rt(np.array([[1,0,0],[0,1,0],[0,0,1]]),np.array([0,0,0]))
            for shoulder_UA,shoulder_UA_mid_est,shoulder_rbt,\
                elbow_UA,elbow_UA_mid_est,\
                wrist_UA,wrist_UA_mid_est\
                in zip(shoulder_UA_traj[0::step],shoulder_UA_mid_est_traj[0::step],shoulder_rbt_traj[0::step],
                       elbow_UA_traj[0::step],elbow_UA_mid_est_traj[0::step],
                       wrist_UA_traj[0::step],wrist_UA_mid_est_traj[0::step]):
                
                # break immediately if figure is closed
                if not plt.get_fignums():
                    break

                i = i+1
                num = i*step

                ax2.clear()
                ax2.set_xlabel('X2')
                ax2.set_xlim(-0.1,1.0)
                ax2.set_ylabel('Y2')
                ax2.set_ylim(-0.5,0.3)
                ax2.set_zlabel('Z2')
                ax2.set_zlim(0.1,1.6)
                ax2.set_box_aspect([1, 1, 1])
                world.plot(frame='w', color='green',length=0.05,ax=ax2)

                shoulder_UA_mid_est.plot(frame=f's{num}-UA-mid-est',color='b',length=0.05,ax=ax2,axislabel=False,axissubscript=False)

                wrist_UA_mid_est.plot(frame=f'w{num}-rbt-mid-est',color='b',length=0.05,ax=ax2,axislabel=False,axissubscript=False)

                elbow_UA_mid_est.plot(frame=f'e{num}-rbt-est',color='b',length=0.05,ax=ax2,axislabel=False,axissubscript=False)

                x_mid_est = np.array([shoulder_UA_mid_est.t[0],elbow_UA_mid_est.t[0],wrist_UA_mid_est.t[0]])
                y_mid_est = np.array([shoulder_UA_mid_est.t[1],elbow_UA_mid_est.t[1],wrist_UA_mid_est.t[1]])
                z_mid_est = np.array([shoulder_UA_mid_est.t[2],elbow_UA_mid_est.t[2],wrist_UA_mid_est.t[2]])
                ax2.plot(x_mid_est,y_mid_est,z_mid_est,marker='o', linestyle='-', color='b')

                color = ['g','k']
                for j,avg_task_point in enumerate(avg_task_points_rbt):
                    avg_task_point_UA = shoulder_rbt*SE3.Trans(avg_task_point)
                    avg_task_point_UA.plot(frame=f'tp{num}-rbt',color=color[j],length=0.05,ax=ax2)
                    
                plt.pause(0.2)

            if not plt.get_fignums(): # break immediately if figure is closed
                break
            elif (not loop):
                plt.show(block=False)
                break
    
    return shoulder_UA_traj,shoulder_UA_mid_est_traj,\
            elbow_UA_traj,elbow_UA_mid_est_traj,\
            wrist_UA_traj,wrist_UA_mid_est_traj,\
            avg_task_points_rbt,avg_task_points_UA

"""
Calculate EngUL Joint Angles
"""
def calc_engUL_joint_angles(shoulder_UA_traj,elbow_UA_traj,wrist_UA_traj,submovement,time,body_param,model,arm_side,see_rbt=False):
    sampling_rate = np.mean(1/np.diff(time,axis=0))
    arm_model_params_d = {'ua_l': body_param['ua'].loc[0],
                                'fa_l': body_param['fa'].loc[0],
                                'ha_l': 0.00,
                                'm_ua': 2.0,
                                'm_fa': 1.1+0.23+0.6}
    arm_lfd = armLFD(arm_model_params_d,model=model,arm_side=arm_side)

    joint_angles = []
    traj = []
    for shoulder_UA,elbow_UA,wrist_UA,cur_sbmvmt,cur_time in zip(shoulder_UA_traj,
                                                            elbow_UA_traj,wrist_UA_traj,submovement,time):
        q_ua = arm_lfd.IK_EngUL(shoulder_UA,elbow_UA,wrist_UA)
        joint_angles.append([0,q_ua[0], q_ua[1], q_ua[2], q_ua[3],0,0,0])
        traj.append([sampling_rate]+cur_time.tolist()+shoulder_UA.t.tolist()+elbow_UA.t.tolist()+wrist_UA.t.tolist()+[q_ua[0], q_ua[1], q_ua[2], q_ua[3]]+cur_sbmvmt.tolist()) # compile all data to deptch cams format
    
    if see_rbt:
        fig = plt.figure()
        arm_model = arm_lfd.UL_visual
        arm_model.plot(q = np.array(joint_angles[0::10]),backend='pyplot',block=True,loop=False,jointaxes=True,eeframe=True,shadow=False,fig=fig)
        plt.close("all")

    traj = pd.DataFrame(traj, columns=['fps','time','x_shld','y_shld','z_shld','x_elbw','y_elbw','z_elbw','x_wrst','y_wrst','z_wrst','q1', 'q2', 'q3', 'q4',"submvmt"])
    return traj

"""
Estimate new joint angles (task parameters) from new task points
- TODO: develop an IK that can recreate that without giving the explicit joint angles 
"""
def IK_task_params(body_param,traj_est,task_points,model='ISB',visualize=False,hand_length=0,arm_side="right"):
    arm_model_params_d = {'ua_l': body_param['ua'].loc[0],
                                'fa_l': body_param['fa'].loc[0],
                                'ha_l': hand_length,
                                'm_ua': 2.0,
                                'm_fa': 1.1+0.23+0.6}
    arm_lfd = armLFD(arm_model_params_d,model=model,arm_side=arm_side)
    arm_model = arm_lfd.UL

    qq_new = []
    qq_new.append(traj_est[['q1','q2','q3','q4']].values[0]) # initial configuration

    for i,task_point in enumerate(task_points):
        index = traj_est[traj_est['submvmt'] == (i+1)].index[-1] # take the last joint configuration of each submovement
        
        TT=SE3.Trans(task_point)
        iter = 0
        success=0
        while (success == 0 and iter < 3):
            iter = iter+1
            # To replace with a custom IK that follows healthy body constraints
            q0 = np.array(traj_est[['q1','q2','q3','q4']].values[index].tolist() + [0,0,0])
            qq, success, iterations, searches, residual=arm_model.ik_GN(TT, q0=q0, mask=[1, 1, 1, 0, 0, 0],tol=1e-6)
        # if success == 0:
        #     raise
        qq[4:] = 0 # ignore the last 3 DOFs for now
        qq_new.append(qq[:4])
        # print(f"Success / Iterations/ Searches:",success,iterations,searches)
        # print("Intended Task Param:",q0*180/np.pi,"\nCalculated Task Param:",qq*180/np.pi)
        # print("Actual Task Point:",task_point)
        # print("Assumed Task Point:",arm_model.fkine(q0).t)
        # print("Estimated Task Point:",arm_model.fkine(qq).t)
        # print()

    qq_new.append(traj_est[['q1','q2','q3','q4']].values[-1]) # final configuration
    # print("Full Estimated Task Params")
    # for i in qq_new:
    #     print(i*180/np.pi)
    # print()
    
    if visualize:
        arm_model_vis = arm_lfd.UL_visual
        fig = plt.figure()
        arm_model_vis.plot(q = np.hstack((np.zeros((np.array(qq_new).shape[0],1)),np.array(qq_new),np.zeros((np.array(qq_new).shape[0],3)))),
                    backend='pyplot',block=False,loop=False,jointaxes=True,eeframe=True,shadow=False,fig=fig,dt=1)
    qq_new = pd.DataFrame(qq_new, columns=["tp0","tp1","tp2","tp3"])
    return qq_new



