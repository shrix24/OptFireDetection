import cv2
import numpy as np
from ImProc_Detect_funcs import ImageProcessor
from signalrcore.hub_connection_builder import HubConnectionBuilder
import logging
from GlobalVars import *

global gps_position, uav_attitude

class ImProc_Detect:
    def __init__(self) -> None:
        self.frame_size = 500
        self.alpha = 1.8
        self.beta = 20
        self.R_thresh = 120
        self.B_thresh = 230
        self.contour_area = 50
        self.gps_position = np.array([0, 0, 0])
        self.uav_attitude = np.array([0, 0, 0])
        
        self.PLATFORM_CONNECTION_URL = "http://127.0.0.1:5001"
        self.USERNAME = "Admin"
        self.PASSWORD = "Distributed"

        # print("Getting Token...")
        # self.payload = {"username": self.USERNAME, "password": self.PASSWORD } #replace these with your own for CC, GC or PC as required
        # self.response = requests.post(self.PLATFORM_CONNECTION_URL + '/authentication/authenticate', json = self.payload)
        # self.token = "Bearer " + self.response.json()["token"] # important to add 'Bearer' to the start of the token here
        # print("Got Token: " + self.token)

        # print("Setting up service handler")
        self.handler = logging.StreamHandler()
        logging.disable() # disable it by default... it's verbose!

        # print("Building Connection to Platform Control")
        global_vars.hub_connection = HubConnectionBuilder().with_url(self.PLATFORM_CONNECTION_URL + "/autopilotHub").configure_logging(logging.DEBUG, socket_trace=True, handler=self.handler).build()

        # print("Signing up to open, close and error events")
        # sign up to start stop and error events
        global_vars.hub_connection.on_open(self.onOpen)
        global_vars.hub_connection.on_close(self.onClose)
        global_vars.hub_connection.on_error(self.onError)

        # print("Signing up to location and attitude broadcasting")
        global_vars.hub_connection.on("BroadcastLocation", self.handleLocation)
        global_vars.hub_connection.on("BroadcastAttitude", self.handleAttitude)

        # print("Starting Connection")
        # start connection
        global_vars.hub_connection.start()

    def handleHeartbeat(self, data):
        print(data[0])

    def handleLocation(self, data):
        # print(data)
        # location is in decimal degrees and altitude is in meters AMSL relative to EGM96 Geiod

        # location is sent as a dictionary and can be accessed as shown (same system for other variables)
        # example assignment to variable inside location structure

        altitudeM_AMSL = data[0]['data']['altM']
        Latitude = data[0]['data']['latDeg']
        Longitude = data[0]['data']['lngDeg']

        self.gps_position = np.array([Latitude, Longitude, altitudeM_AMSL])
        # be aware that in python if you want to assign a variable outside the scope of the function you must declare it as 'global'
    
    def handleAttitude(self, data):
        # print(data)
        roll = data[0]['data']['rollDeg']
        yaw = data[0]['data']['yawDeg']
        pitch = data[0]['data']['pitchDeg']

        self.uav_attitude = np.array([roll, yaw, pitch])
        # Attitude is in degrees

    # declare connection event handlers
    def onOpen():
        print("Connection opened")

    def onClose():
        print("Connection closed")

    def onError(data):
        print("Error | %s" % data.error)

    def detect(self, raw_frame):
        # print("Starting Fire Detection")
        try:
            # print("Step 1: Preprocessing")
            frame = raw_frame
            # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (self.frame_size, self.frame_size), cv2.INTER_AREA)
            original_frame = frame.copy()
            # cv2.imshow("Original Frame", frame)
            ImProc = ImageProcessor(frame)
            ImProc.preprocessor()

            # print("Step 2: Fire Indices")
            ImProc.vbi_idx()
            # cv2.imshow("VBI", vbi)
            ImProc.fi_idx().astype(np.uint8)
            # cv2.imshow("FI", fi)
            ImProc.ffi_idx(self.alpha).astype(np.uint8)
            # cv2.imshow("FFI", ffi)
            ImProc.calc_tf(self.alpha)

            ImProc.ffi_binarize()

            ImProc.erosion().astype(np.uint8)
            ImProc.dilation().astype(np.uint8)
            ffi_blurred = ImProc.blur().astype(np.uint8)
            D_f = cv2.bitwise_and(frame, frame, mask=ffi_blurred)
            # cv2.imshow("Fire Area", ffi_dilated)

            # Apply color rules
            rule1_result = ImProc.rule_1(self.beta).astype(np.uint8)
            # cv2.imshow("Rule 1", rule1_result)
            rule2_result = ImProc.rule_2(self.R_thresh, self.B_thresh).astype(np.uint8)
            # cv2.imshow("Rule 2", rule2_result)
            rule3_result = ImProc.rule_3().astype(np.uint8)
            # cv2.imshow("Rule 3", rule3_result)
            D_s = cv2.bitwise_and(rule1_result, rule2_result).astype(np.uint8)
            D_s = cv2.bitwise_and(rule3_result, D_s).astype(np.uint8)
            # cv2.imshow("Smoke Area", D_s)

            D_fs_bin = cv2.bitwise_or(ffi_blurred, D_s).astype(np.uint8)
            D_fs = cv2.bitwise_and(frame, frame, mask=D_fs_bin).astype(np.uint8)
            # cv2.imshow("Fire Area Final", D_fs)

            # print("Step 3: Wavelet Transforms")
            E_result = ImProc.wavelet_transform(D_fs, frame)
            # cv2.imshow("Wavelet Result", E_result)

            D_result = cv2.bitwise_and(D_fs_bin, E_result).astype(np.uint8)
            # final_result = cv2.bitwise_and(frame, frame, mask=D_result)

            contours, _ = cv2.findContours(D_result, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            areas = []

            if contours:
                # print("Detecting Contours")
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area < self.contour_area:
                        areas.append(area)
                        continue
                    x, y, w, h = cv2.boundingRect(contour)
                    frame = cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)

                if areas:
                    # print("Calculating Centroid")
                    areas = np.array(areas)
                    max_area_idx = np.argmax(areas)
                    x_m, y_m, w_m, h_m = cv2.boundingRect(contours[max_area_idx])
                    centroid = (x_m + w_m/2, y_m + h_m/2)
                    global_vars.img_coords = centroid
                else:
                    global_vars.img_coords = np.array([0, 0])

            global_vars.og_image_to_transmit = original_frame
            global_vars.image_to_transmit = frame

            # print(self.gps_position)

            if self.gps_position.size > 0 and self.uav_attitude.size > 0:
                global_vars.gps_position = self.gps_position
                global_vars.uav_attitude = self.uav_attitude

        except Exception as error:
            print(error)


if __name__=="__main__":
    # vision_module = Detector()
    # vision_module.detect()
    pass