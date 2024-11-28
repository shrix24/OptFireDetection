import cv2
import joblib
import numpy as np
from skimage.util import view_as_blocks
from Classifier_Processing import Window_Wavelet_Features
from sklearn.cluster import DBSCAN
import logging
from signalrcore.hub_connection_builder import HubConnectionBuilder
from GlobalVars import global_vars

class Classifier_Detect:
    def __init__(self) -> None:
        self.LGBM_Model = joblib.load(r"C:\development\XPrizev2\LGBM_Wavelet_Parameters")
        self.video_path = r"C:\Users\Aditya Shrikhande\Downloads\15184522-uhd_3840_2160_24fps.mp4"
        self.cap = cv2.VideoCapture(self.video_path)
        self.frame_size = 600
        self.bsize = 60

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

    def classify(self, block, LGBM_Model):
        img_features = Window_Wavelet_Features(block).feature_extract_infer(block)
        test_features = np.expand_dims(img_features, axis=0)
        test_for_RF = np.reshape(test_features, (1, -1))
        test_prediction = LGBM_Model.predict(test_for_RF)
        test_prob = LGBM_Model.predict_proba(test_for_RF)

        if test_prediction == 0 and test_prob[0][0] >= 0.85:
            return test_prediction
        else:
            return

    def pre_localize(self, test_preds):
        idx = np.where(test_preds==0)
        zero_idx = list(zip(idx[0], idx[1]))
        zero_idx = np.array(zero_idx)

        if zero_idx.size == 0:
            return np.array([])
        
        centroid_coordinates = np.zeros(zero_idx.shape)
        
        for i in range(zero_idx.shape[0]):
            if zero_idx[i, 0] == 0:
                x_f = 0 + 1.5*(self.bsize)
            else:
                x_f = 0 + zero_idx[i, 0]*(self.bsize) + 1.5*self.bsize

            if zero_idx[i, 1] == 0:
                y_f = 0 + 1.5*(self.bsize)
            else:
                y_f = 0 + zero_idx[i, 1]*(self.bsize) + 1.5*self.bsize

            centroid_coordinates[i, 0] = y_f
            centroid_coordinates[i, 1] = x_f

        return centroid_coordinates

    def outlier_rejection(self, centroid_coordinates, epsilon, DBSCAN):
        if centroid_coordinates.size == 0:
            return np.array([])
        
        dbscan = DBSCAN(eps=epsilon, min_samples=2)
        labels = dbscan.fit_predict(centroid_coordinates)

        cleaned_coordinates = centroid_coordinates[labels!=-1]
        return cleaned_coordinates

    def detect(self, raw_frame):
        try:
            self.frame_count = 0

            frame = raw_frame
            frame = cv2.resize(frame, (self.frame_size, self.frame_size))
            original_frame = frame.copy()

            if self.frame_count%30 == 0 or self.frame_count == 0:
                frame_blocks = view_as_blocks(frame, (self.bsize, self.bsize, 3))
                test_preds = np.ones((int(self.frame_size/self.bsize), int(self.frame_size/self.bsize)))

                reshape_frame_blocks = frame_blocks.reshape(-1, self.bsize, self.bsize, 3)
                results = np.zeros(reshape_frame_blocks.shape[0])

                for block in range(reshape_frame_blocks.shape[0]):
                    results[block] = self.classify(reshape_frame_blocks[block], self.LGBM_Model)

                test_preds = results.reshape(frame_blocks.shape[:2])
                centroid_coordinates = self.pre_localize(test_preds)
                centroid_coordinates = self.outlier_rejection(centroid_coordinates, self.bsize, DBSCAN)

                if centroid_coordinates.size != 0:
                    if centroid_coordinates.size == 2:
                        x_max = int(np.max(centroid_coordinates[:, 0]))
                        x_min = int(np.min(centroid_coordinates[:, 0]))
                        y_max = int(np.max(centroid_coordinates[:, 1]))
                        y_min = int(np.min(centroid_coordinates[:, 1]))

                        cv2.rectangle(frame, (x_min-0.5*self.bsize, y_min-0.5*self.bsize), (x_max+0.5*self.bsize, y_max+0.5*self.bsize), (0, 255, 0), 2)
                        img_coords = ((x_max+x_min)/2, (y_max+y_min)/2)
                        global_vars.img_coords = img_coords
                    
                    else:      
                        x_max = int(np.max(centroid_coordinates[:, 0]))
                        x_min = int(np.min(centroid_coordinates[:, 0]))
                        y_max = int(np.max(centroid_coordinates[:, 1]))
                        y_min = int(np.min(centroid_coordinates[:, 1]))

                        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                        img_coords = ((x_max+x_min)/2, (y_max+y_min)/2)
                        global_vars.img_coords = img_coords

                else:
                    global_vars.img_coords = np.array([0, 0])

                global_vars.og_image_to_transmit = original_frame
                global_vars.image_to_transmit = frame

                if self.gps_position.size > 0 and self.uav_attitude.size > 0:
                    global_vars.gps_position = self.gps_position
                    global_vars.uav_attitude = self.uav_attitude

            self.frame_count += 1
        
        except Exception as error:
            print(error)


if __name__ == "__main__":
    # vision_module = ClassifierDetect()
    # vision_module.detect()
    pass