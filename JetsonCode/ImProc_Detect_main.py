import cv2
import numpy as np
from ImProc_Detect_funcs import ImageProcessor
from signalrcore.hub_connection_builder import HubConnectionBuilder
import time
import logging

class ImProc_Detect:
    def __init__(self) -> None:
        self.video_path = r"C:\Users\Aditya Shrikhande\Downloads\15184524-uhd_3840_2160_24fps.mp4"
        self.cap = cv2.VideoCapture(self.video_path)
        self.frame_size = 500
        self.alpha = 1.8
        self.beta = 20
        self.R_thresh = 120
        self.B_thresh = 230
        self.contour_area = 50
        
        self.PLATFORM_CONNECTION_URL = "http://127.0.0.1:5000"
        self.USERNAME = "Admin"
        self.PASSWORD = "Distributed"

        # print("Getting Token...")
        # self.payload = {"username": self.USERNAME, "password": self.PASSWORD } #replace these with your own for CC, GC or PC as required
        # self.response = requests.post(self.PLATFORM_CONNECTION_URL + '/authentication/authenticate', json = self.payload)
        # self.token = "Bearer " + self.response.json()["token"] # important to add 'Bearer' to the start of the token here
        # print("Got Token: " + self.token)

        self.handler = logging.StreamHandler()
        logging.disable() # disable it by default... it's verbose!

        self.hub_connection = HubConnectionBuilder().with_url(self.PLATFORM_CONNECTION_URL + "/autopilotHub").configure_logging(logging.DEBUG, socket_trace=True, handler=self.handler).build()

        # sign up to start stop and error events
        self.hub_connection.on_open(self.onOpen)
        self.hub_connection.on_close(self.onClose)
        self.hub_connection.on_error(self.onError)

        self.hub_connection.on("BroadcastLocation", self.handleLocation)
        self.hub_connection.on("BroadcastAttitude", self.handleAttitude)

        # start connection
        self.hub_connection.start()

        # keep program alive
        pressedEnter = None
        while pressedEnter != "":
            pressedEnter = input("")
            time.sleep(1)

        # end connection
        self.hub_connection.stop()

    def handleHeartbeat(data):
        print(data[0])

    def handleLocation(data):
        print(data)
        # location is in decimal degrees and altitude is in meters AMSL relative to EGM96 Geiod

        # location is sent as a dictionary and can be accessed as shown (same system for other variables)
        # example assignment to variable inside location structure
        altitudeM_AMSL = data[0]['altM']
        Latitude = data[0]['latDeg']
        Longitude = data[0]['lngDeg']

        global gps_position
        gps_position = np.array[Latitude, Longitude, altitudeM_AMSL]
        # be aware that in python if you want to assign a variable outside the scope of the function you must declare it as 'global'
    
    def handleAttitude(data):
        print(data[0])
        global attitude
        attitude = data[0]
        # Attitude is in degrees

    # declare connection event handlers
    def onOpen():
        print("Connection opened")

    def onClose():
        print("Connection closed")

    def onError(data):
        print("Error | %s" % data.error)

    def detect(self, raw_frame):
        if self.cap.isOpened():
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # fourcc = cv2.VideoWriter.fourcc(*'XVID')
        # output = cv2.VideoWriter(output_path, fourcc, 24, (500, 500))

        self.frame_count = 0

        if self.frame_count%30==0 or self.frame_count==0:
            original_frame = raw_frame.copy()
            frame = raw_frame
            # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (self.frame_size, self.frame_size), cv2.INTER_AREA)
            cv2.imshow("Original Frame", frame)
            ImProc = ImageProcessor(frame)
            ImProc.preprocessor()

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

            E_result = ImProc.wavelet_transform(D_fs, frame)
            # cv2.imshow("Wavelet Result", E_result)

            D_result = cv2.bitwise_and(D_fs_bin, E_result).astype(np.uint8)
            final_result = cv2.bitwise_and(frame, frame, mask=D_result)

            contours, _ = cv2.findContours(D_result, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            areas = []

            if contours:
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area < self.contour_area:
                        areas.append(area)
                        continue
                    x, y, w, h = cv2.boundingRect(contour)
                    frame = cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)

                if areas:
                    areas = np.array(areas)
                    max_area_idx = np.argmax(areas)
                    x_m, y_m, w_m, h_m = cv2.boundingRect(contours[max_area_idx])
                    centroid = (x_m + w_m/2, y_m + h_m/2)
                    # print(centroid)
                
            # cv2.imshow("Final Result", final_result)
            # cv2.imshow("Detections", frame)

            self.og_image_to_transmit = original_frame
            self.image_to_transmit = frame
            self.img_coords = centroid
            self.gps_position = gps_position
            self.uav_attitude = attitude

        self.frame_count += 1
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

        # # output.release()
        # self.cap.release()
        # cv2.destroyAllWindows()


if __name__=="__main__":
    # vision_module = Detector()
    # vision_module.detect()
    pass