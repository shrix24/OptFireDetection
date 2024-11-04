import numpy as np
import typing
import math
from numpy.typing import NDArray
import cv2


class Image2World:
    def __init__(self, intrinsic_params, extrinsic_params, vehicle_pose) -> None:
        self.x_focal: float = intrinsic_params[0]
        self.y_focal: float = intrinsic_params[1]
        self.skew: float = intrinsic_params[2]
        self.P_x: float = intrinsic_params[3]
        self.P_y: float = intrinsic_params[4]

        self.x_offset: float = extrinsic_params[0]
        self.y_offset: float = extrinsic_params[1]
        self.z_offset: float = extrinsic_params[2]
        self.azimuth: float = extrinsic_params[3]
        self.elevation: float = extrinsic_params[4]
        
        self.x_UAV: float = vehicle_pose[0]
        self.y_UAV: float = vehicle_pose[1]
        self.z_UAV: float = vehicle_pose[2]
        self.phi: float = vehicle_pose[3]
        self.theta: float = vehicle_pose[4]
        self.psi: float = vehicle_pose[5]

    def Inertial2Vehicle(self) -> NDArray[np.float64]:
        T_i2v: NDArray = np.ndarray((4, 4), dtype=np.float64)
        print(type(T_i2v[0:3, 0:3]))
        T_i2v[0:3, 0:3] = np.eye(3, 3, dtype=np.float64)
        T_i2v[3, 0:3] = np.zeros((1, 3), dtype=np.float64)
        T_i2v[3, 3] = np.float64(1.0)

        d_i2v: NDArray = np.ndarray((3,), dtype=np.float64)
        d_i2v[0] = self.x_UAV
        d_i2v[1] = self.y_UAV
        d_i2v[2] = -1*self.z_UAV

        T_i2v[0:3, 3] = -1*d_i2v

        self.T_i2v = T_i2v
    
    def Vehicle2Body(self) -> NDArray[np.float64]:
        T_v2b: NDArray = np.ndarray((4, 4), dtype=np.float64)
        
        R_v2b: NDArray = np.ndarray((3, 3), dtype=np.float64)
        R_v2b[0, 0] = math.cos(self.theta)*math.cos(self.psi)
        R_v2b[0, 1] = math.cos(self.theta)*math.sin(self.psi)
        R_v2b[0, 2] = -1*math.sin(self.theta)
        R_v2b[1, 0] = math.sin(self.phi)*math.sin(self.theta)*math.cos(self.psi) - math.cos(self.phi)*math.sin(self.psi)
        R_v2b[1, 1] = math.sin(self.phi)*math.sin(self.theta)*math.sin(self.psi) + math.cos(self.theta)*math.cos(self.psi)
        R_v2b[1, 2] = math.sin(self.theta)*math.cos(self.theta)
        R_v2b[2, 0] = math.cos(self.phi)*math.sin(self.theta)*math.cos(self.psi) + math.sin(self.phi)*math.sin(self.psi)
        R_v2b[2, 1] = math.cos(self.phi)*math.sin(self.theta)*math.sin(self.psi) - math.sin(self.phi)*math.cos(self.psi)
        R_v2b[2, 2] = math.cos(self.phi)*math.cos(self.theta)

        T_v2b[0:3, 0:3] = R_v2b
        T_v2b[3, 0:3] = np.zeros((1, 3), dtype=np.float64)
        T_v2b[3, 3] = np.float64(1)
        T_v2b[0:3, 3] = np.zeros((3,), dtype=np.float64)

        self.T_v2b = T_v2b
    
    def Body2Camera(self):
        T_b2g: NDArray = np.ndarray((4, 4), dtype=np.float64)

        R_b2g: NDArray = np.ndarray((3, 3), dtype=np.float64)
        R_b2g[0, 0] = math.cos(self.elevation)*math.cos(self.azimuth)
        R_b2g[0, 1] = math.cos(self.elevation)*math.sin(self.azimuth)
        R_b2g[0, 2] = math.sin(self.elevation)
        R_b2g[1, 0] = -1*math.sin(self.elevation)
        R_b2g[1, 1] = math.cos(self.azimuth)
        R_b2g[1, 2] = np.float64(0)
        R_b2g[2, 0] = -1*math.sin(self.elevation)*math.cos(self.azimuth)
        R_b2g[2, 1] = -1*math.sin(self.elevation)*math.sin(self.azimuth)
        R_b2g[2, 2] = math.cos(self.elevation)

        d_b2g = np.ndarray((3,), dtype=np.float64)
        d_b2g[0] = self.x_offset
        d_b2g[1] = self.y_offset
        d_b2g[2] = self.z_offset

        T_b2g[0:3, 0:3] = R_b2g
        T_b2g[0:3, 3] = -1*d_b2g
        T_b2g[3, 0:3] = np.zeros((3,), dtype=np.float64)
        T_b2g[3, 3] = np.float64(1)

        self.T_b2g = T_b2g
    
    def g2c(self):
        T_g2c: NDArray = np.eye(4, 4, dtype=np.float64)

        self.T_g2c = T_g2c
    
    def CamCalibration(self):
        C_c = np.array([[self.x_focal, self.skew, self.P_x, 1e-10],
                        [1e-10, self.y_focal, self.P_y, 1e-10],
                        [1e-10, 1e-10, 1e-10, 1e-10],
                        [1e-10, 1e-10, 1e-10, 1]])
        
        self.C_c = C_c
    
    def DepthCalc(self):
        inv_rot_cc = np.linalg.inv((self.T_g2c @ self.T_b2g @ self.T_v2b @ self.T_i2v))
        # print(inv_rot_cc)
        inv_rot_obj = np.linalg.inv((self.C_c @ self.T_g2c @ self.T_b2g @ self.T_v2b @ self.T_i2v))
        print(inv_rot_obj)
        z_cc = inv_rot_cc[2]
        z_obj = inv_rot_obj[2]
        print(z_cc)
        print(z_obj)
        depth: float = np.float64(z_cc/(z_cc - z_obj))

        self.depth = depth
        return inv_rot_obj
    
    def Convert(self, img_coordinates):
        self.Inertial2Vehicle()
        self.Vehicle2Body()
        self.Body2Camera()
        self.g2c()
        self.CamCalibration()
        inv_rot_obj = self.DepthCalc()

        q = np.ndarray((4, 1), dtype=np.float64)
        q[0] = img_coordinates[0]
        q[1] = img_coordinates[1]
        q[2] = 1
        q[3] = 1

        # print(self.depth)
        Lambd = np.array([[self.depth, 0, 0, 0],
                          [0, self.depth, 0, 0],
                          [0, 0, self.depth, 0],
                          [0, 0, 0, 1]])
        


        P_obj = inv_rot_obj @ Lambd @ q

        return P_obj
    

if __name__ == "__main__":
    pass






