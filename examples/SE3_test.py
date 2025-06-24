# #%%
# # SE3 plotting and frame relations 
# # Create the initial frame p
# p = SE3.Rt(R=SO3(), t=[0, 0, 0])
# p.plot(frame='p', color='blue')

# # Create and plot a second frame p2
# p2 = SE3.Rt(R=SO3() * SO3.Rz(-90, 'deg') * SO3.Rx(90, 'deg'), t=[0, 0, 0]) 
# # follow this intrinsic rotation order (rotate abt z by -90, rotate about x by 90)
# # p2.R gives rotation from p to p2

# p2.plot(frame='p2', color='red')

# # Add a vector in the x-direction of the p frame
# origin = p.t  # origin of frame p
# v1 = [1,1,1]
# plt.quiver(
#     origin[0], origin[1], origin[2],
#     v1[0], v1[1], v1[2],
#     length=1.0, color='green', normalize=True
# )

# v2 = np.matmul(np.linalg.inv(p2.R),v1)
# print(v2)
# plt.show()
# %%
import matplotlib.pyplot as plt
from spatialmath import SE3,SO3
from scipy.spatial.transform import Rotation as R


quaternion = [0,0,0,1]  # 90° rotation around z-axis

# Create the SO(3) rotation object
rotation = R.from_quat(quaternion)
p = SO3(rotation.as_matrix())
p.plot()
plt.show()