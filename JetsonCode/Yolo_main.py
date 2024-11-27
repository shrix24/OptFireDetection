import numpy as np
import cv2
from ultralytics import YOLO
import logging
from signalrcore.hub_connection_builder import HubConnectionBuilder


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

        print("Building Connection to Platform Control")
        self.hub_connection = HubConnectionBuilder().with_url(self.PLATFORM_CONNECTION_URL + "/autopilotHub").configure_logging(logging.DEBUG, socket_trace=True, handler=self.handler).build()

        print("Signing up to open, close and error events")
        # sign up to start stop and error events
        self.hub_connection.on_open(self.onOpen)
        self.hub_connection.on_close(self.onClose)
        self.hub_connection.on_error(self.onError)

        print("Signing up to location and attitude broadcasting")
        self.hub_connection.on("BroadcastLocation", self.handleLocation)
        self.hub_connection.on("BroadcastAttitude", self.handleAttitude)

        print("Starting Connection")
        # start connection
        self.hub_connection.start()

    def handleHeartbeat(self, data):
        print(data[0])

    def handleLocation(self, data):
        # print(data)
        # location is in decimal degrees and altitude is in meters AMSL relative to EGM96 Geiod

        # location is sent as a dictionary and can be accessed as shown (same system for other variables)
        # example assignment to variable inside location structure
        altitudeM_AMSL = data['data']['altM']
        Latitude = data['data']['latDeg']
        Longitude = data['data']['lngDeg']

        self.gps_position = np.array[Latitude, Longitude, altitudeM_AMSL]
        # be aware that in python if you want to assign a variable outside the scope of the function you must declare it as 'global'
    
    def handleAttitude(self, data):
        # print(data)
        roll = data['data']['rollDeg']
        yaw = data['data']['yawDeg']
        pitch = data['data']['pitchDeg']
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
        # self.cap = cv2.VideoCapture(self.video_path)
        # self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        # self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))


        # self.output_video = cv2.VideoWriter('output_video.mp4',
        #                         cv2.VideoWriter_fourcc(*'mp4v'),
        #                         self.fps,
        #                         (self.frame_width, self.frame_height))
        self.frame_count = 0
        frame = cv2.resize(frame, (640, 480), cv2.INTER_AREA)
        # Run inference on the current frame using the custom model
        results = self.model.predict(frame)

        # Visualize the predictions directly on the frame
        annotated_frame = results[0].plot()  # Annotated frame with bounding boxes

        # Write the annotated frame to the output video
        # output_video.write(annotated_frame)
        
        # Display the frame (optional)
        # cv2.imshow('YOLO Detection', annotated_frame)
        self.frame_count += 1
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()


if __name__ == "__main__":
    # vision_module = YOLO_Detect()
    # vision_module.detect()
    pass