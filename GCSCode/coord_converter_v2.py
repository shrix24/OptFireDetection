import numpy as np
import requests

class Image2World:
    def __init__(self, img_coordinates, camera_res, FoV, vehicle_pose) -> None:
        self.x_coord = img_coordinates[0]
        self.y_coord = img_coordinates[1]
        self.h_FoV = FoV[0]
        self.v_FoV = FoV[1]
        self.h_res = camera_res[0]
        self.v_res = camera_res[1]
        self.h_unit_offset = self.h_FoV/self.h_res
        self.v_unit_offset = self.v_FoV/self.v_res

        self.x_center = self.x_res/2
        self.y_center = self.y_res/2

        self.vehicle_lat = vehicle_pose[0]
        self.vehicle_lon = vehicle_pose[1]
        self.vehicle_alt = vehicle_pose[2]
        self.vehicle_pitch = vehicle_pose[3]

        self.terrain_server_url = "http://127.0.0.1:5139/api/Terrain/getTerrainPoint"

    def ned2gps(self, ref_gps, ned_point):
        # WGS84 constants
        a = 6378137.0  # Semi-major axis
        b = 6356752.3142  # Semi-minor axis
        e2 = 1 - (b**2 / a**2)  # Square of first eccentricity

        def geodetic2ecef(ref_gps):
            lat_rad = np.radians(ref_gps[0])
            lon_rad = np.radians(ref_gps[1])
            N = a / np.sqrt(1 - e2 * np.sin(lat_rad)**2)
            
            X = (N + ref_gps[2]) * np.cos(lat_rad) * np.cos(lon_rad)
            Y = (N + ref_gps[2]) * np.cos(lat_rad) * np.sin(lon_rad)
            Z = ((1 - e2) * N + ref_gps[2]) * np.sin(lat_rad)

            return np.array([X, Y, Z])
        
        def ned2ecef(ned_point, ref_gps):
            # Reference point ECEF coordinates
            ref_ecef = geodetic2ecef(ref_gps)
            # Compute rotation matrix from ECEF to NED
            ref_lat = np.radians(ref_lat)
            ref_lon = np.radians(ref_lon)
            
            R = np.array([
                [-np.sin(ref_lat) * np.cos(ref_lon), -np.sin(ref_lat) * np.sin(ref_lon), np.cos(ref_lat)],
                [-np.sin(ref_lon), np.cos(ref_lon), 0],
                [-np.cos(ref_lat) * np.cos(ref_lon), -np.cos(ref_lat) * np.sin(ref_lon), -np.sin(ref_lat)]
            ])
            
            # Inverse rotation (transpose of R)
            R_inv = np.linalg.inv(R)
            
            # NED to ECEF difference vector
            ned_vector = np.array([ned_point[0], ned_point[1], ned_point[2]])
            delta_ecef = R_inv @ ned_vector
            
            # Compute the ECEF coordinates of the target point
            target_ecef = ref_ecef + delta_ecef
            return target_ecef

        def ecef2geodetic(target_ecef):
            p = np.sqrt(target_ecef[0]**2 + target_ecef[1]**2)
            theta = np.arctan2(target_ecef[2] * a, p * b)
            
            lon = np.arctan2(target_ecef[1], target_ecef[0])
            lat = np.arctan2(target_ecef[2] + (e2 * (b**2 / a**2)) * np.sin(theta)**3, 
                            p - e2 * a * np.cos(theta)**3)
            N = a / np.sqrt(1 - e2 * np.sin(lat)**2)
            alt = p / np.cos(lat) - N
            
            # Convert radians to degrees
            lat = np.degrees(lat)
            lon = np.degrees(lon)
            
            return np.array([lat, lon, alt])

        target_ecef = ned2ecef(ned_point, ref_gps)
        target_gps = ecef2geodetic(target_ecef)

        return target_gps

    def calc_angles(self):
        self.x_offset = self.x_coord - self.x_center
        self.y_offset = self.y_center - self.y_coord

        self.h_offset = 0
        self.v_offset = 0

        self.h_offset = self.x_offset*self.h_unit_offset
        self.v_offset = self.y_offset*self.v_unit_offset

        self.azimuth = np.deg2rad(self.h_offset)
        self.elevation = np.deg2rad(144.7 - self.vehicle_pitch) + np.deg2rad(self.v_offset)

    def propagate_vector(self, counter):
        if counter == 0:
            self.prop_vec_origin = np.array([0, 0, 0])
        else:
            self.prop_vec_origin = self.prop_vec

        N = 10*np.cos(self.elevation)*np.cos(self.azimuth)
        E = 10*np.cos(self.elevation)*np.sin(self.azimuth)
        D = -10*np.sin(self.elevation)
        self.prop_vec = self.prop_vec_origin + np.array([N, E, D])
        
        counter += 1
        
        return counter

    def check_terrain(self):
        self.prop_vec_gps = self.ned2gps(np.array([self.vehicle_lat, self.vehicle_lat, self.vehicle_alt]), self.prop_vec)

        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }

        json_data = {
            "latDeg": self.prop_vec_gps[0],
            "lngDeg": self.prop_vec_gps[1]
        }

        response = requests.post(self.terrain_server_url, json=json_data, headers=headers)

        if response == 200:
            print("Success: ", response.json())
            server_response = response.json()
            self.terrain_check = server_response["success"]
        else:
            print("Failed", response.status_code)

        return self.terrain_check

    def main(self):
        self.calc_angles()
        counter = 0
        counter = self.propagate_vector(counter)
        terrain_collision = self.check_terrain()
    
        while terrain_collision == False:
            counter = self.propagate_vector(counter)
            terrain_collision = self.check_terrain()
        
        print("Target Coordinates Determined!", self.prop_vec_gps)

        return self.prop_vec_gps

if __name__ == "__main__":
    pass