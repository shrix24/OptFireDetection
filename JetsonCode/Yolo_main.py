import numpy as np
import cv2
from ultralytics import YOLO
import logging
from signalrcore.hub_connection_builder import HubConnectionBuilder
from GlobalVars import global_vars


class YOLO_Detect:
    def __init__(self) -> None:
        # self.video_path = r"C:\Users\Aditya Shrikhande\Downloads\15184524-uhd_3840_2160_24fps.mp4"
        self.model = YOLO(r"C:\development\XPrizev3\yolov8s\new_model.pt")

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

        print("Setting up service handler")
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
        self.frame_count = 0

        try:
            if self.frame_count%30 == 0 or self.frame_count == 0:
                x_coords = []
                y_coords = []

                frame = cv2.resize(frame, (640, 480), cv2.INTER_AREA)
                og_image = frame.copy()
                # Run inference on the current frame using the custom model
                results = self.model.predict(frame)

                # Visualize the predictions directly on the frame
                annotated_frame = results[0].plot()  # Annotated frame with bounding boxes

                x_coords = []
                y_coords = []

                for result in results:
                    boxes = result.boxes

                    if not boxes:
                        global_vars.img_coords = np.array([0, 0])
                        break

                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cls = box.cls[0]

                        if cls == 1:
                            x_coords.append(x1)
                            x_coords.append(x2)
                            y_coords.append(y1)
                            y_coords.append(y2)

                x_mean = np.mean(np.array(x_coords))
                y_mean = np.mean(np.array(y_coords))
                global_vars.img_coords = np.array([x_mean, y_mean])

                global_vars.image_to_transmit = frame
                global_vars.og_image_to_transmit = annotated_frame

                if self.gps_position.size > 0 and self.uav_attitude.size > 0:
                    global_vars.gps_position = self.gps_position
                    global_vars.uav_attitude = self.uav_attitude

            self.frame_count += 1

        except Exception as error:
            print(error)

if __name__ == "__main__":
    # vision_module = YOLO_Detect()
    # vision_module.detect()
    pass