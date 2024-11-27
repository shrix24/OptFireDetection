import numpy as np
import requests
import pymap3d
from geographiclib.geodesic import Geodesic

class Image2World:
    def __init__(self, img_coords, img_size, FoV, vehicle_pose) -> None:
        self.x_coord = img_coords[0]
        self.y_coord = img_coords[1]
        self.h_FoV = FoV[0]
        self.v_FoV = FoV[1]
        self.h_size = img_size[0]
        self.v_size = img_size[1]
        self.h_unit_offset = self.h_FoV/self.h_size
        self.v_unit_offset = self.v_FoV/self.v_size

        self.x_center = self.h_size/2
        self.y_center = self.v_size/2

        self.vehicle_lat = vehicle_pose[0]
        self.vehicle_lon = vehicle_pose[1]
        self.vehicle_alt = vehicle_pose[2]
        self.vehicle_pitch = vehicle_pose[3]

        self.terrain_server_url = "http://127.0.0.1:5139/api/Terrain/getTerrainPoint"
        self.terrain_check = False

    def calc_angles(self):
        self.x_offset = self.x_coord - self.x_center
        self.y_offset = self.y_center - self.y_coord

        self.h_offset = 0
        self.v_offset = 0

        self.h_offset = self.x_offset*self.h_unit_offset
        self.v_offset = self.y_offset*self.v_unit_offset

        self.azimuth = self.h_offset
        self.elevation = 144.7 - self.vehicle_pitch + self.v_offset

    def geodetic2ecef(self):
        # WGS84 constants
        a = 6378137.0  # Semi-major axis
        b = 6356752.3142  # Semi-minor axis
        e = np.sqrt(1 - (b**2 / a**2))  # Square of first eccentricity

        lat_rad = np.radians(self.vehicle_lat)
        lon_rad = np.radians(self.vehicle_lon)
        N = a / np.sqrt(1 - e**2 * np.sin(lat_rad)**2)

        X = (N + self.vehicle_alt) * np.cos(lat_rad) * np.cos(lon_rad)
        Y = (N + self.vehicle_alt) * np.cos(lat_rad) * np.sin(lon_rad)
        Z = ((1 - e**2) * N + self.vehicle_alt) * np.sin(lat_rad)

        return (X, Y, Z)
    
    def aer2gps(self, srange):
        (self.ref_x, self.ref_y, self.h0) = self.geodetic2ecef()
        (target_n, target_e, target_d) = pymap3d.aer2ned(self.azimuth, self.elevation, srange)
        (target_x, target_y, target_z) = pymap3d.ned2ecef(target_n, target_e, target_d, self.vehicle_lat, self.vehicle_lon, self.h0)
        (target_lat, target_lon, target_alt) = pymap3d.ecef2geodetic(target_x, target_y, target_z)

        return (target_lat, target_lon, target_alt)


    def propagate_vector(self, counter, srange):
        if counter == 0:
            (target_lat, target_lon, _) = self.aer2gps(srange)
        else:
            (target_lat, target_lon, _) = self.aer2gps(srange+counter)

        return (target_lat, target_lon)
        
    def check_terrain(self):
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }

        json_data = {
            "latDeg": self.target_lat,
            "lngDeg": self.target_lon
        }

        response = requests.post(self.terrain_server_url, json=json_data, headers=headers)

        if response.status_code == 200:
            print("Server response", response.json())
            server_response = response.json()

            if server_response['failureReasons']:
                failure_reasons = server_response['failureReasons'][0].split("-")
                if failure_reasons[1] == " Location not within local terrain file limits":
                    self.terrain_check = -1
                    return self.terrain_check
            else:
                self.terrain_check = server_response["success"]
                return self.terrain_check
        
        else:
            print("Error contacting terrain server", response.status_code)


    def main(self):
        self.calc_angles()
        # print(self.azimuth)
        # print(self.elevation)

        counter = 0
        srange = 10
        
        while self.terrain_check == False:
            (self.target_lat, self.target_lon) = self.propagate_vector(counter, srange)
            # print(self.h0)
            counter += 1
            # print(counter)
            self.terrain_check = self.check_terrain()
            
            if self.terrain_check == -1:
                print("Location not within terrain file limits")
                break

            if self.terrain_check == True:
                print("Target coordinates found!", (self.target_lat, self.target_lon))

        return np.array([self.target_lat, self.target_lon])


if __name__ == "__main__":
    # img_coordinates = np.array([0, 0])
    # img_size = (500, 500)
    # FoV = (140, 110)
    # vehicle_pose = np.array([50.8119158, -1.212601, 10.0999, 2.56])
    # converter = Image2World(img_coordinates, img_size, FoV, vehicle_pose)
    # target_coords = converter.main()
    pass