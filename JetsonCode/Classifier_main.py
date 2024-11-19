import cv2
import joblib
import numpy as np
from skimage.util import view_as_blocks
from Classifier_Processing import Window_Wavelet_Features
from sklearn.cluster import DBSCAN
import time
import logging
from signalrcore.hub_connection_builder import HubConnectionBuilder

class Classifier_Detect:
    def __init__(self) -> None:
        self.LGBM_Model = joblib.load(r"C:\development\XPrizev2\LGBM_Wavelet_Parameters")
        self.video_path = r"C:\Users\Aditya Shrikhande\Downloads\15184522-uhd_3840_2160_24fps.mp4"
        self.cap = cv2.VideoCapture(self.video_path)
        self.frame_size = 600
        self.bsize = 60

        self.PLATFORM_CONNECTION_URL = "http://127.0.0.1:5000"
        self.USERNAME = "Admin"
        self.PASSWORD = "Distributed"

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
        centroid_coordinates = np.zeros(zero_idx.shape)

        for i in range(zero_idx.shape[0]):
            if zero_idx[i, 0] == 0:
                x_f = 0 + 0.5*self.bsize
            else:
                x_f = 0 + zero_idx[i, 0]*self.bsize + 0.5*self.bsize

            if zero_idx[i, 1] == 0:
                y_f = 0 + 0.5*self.bsize
            else:
                y_f = 0 + zero_idx[i, 1]*self.bsize + 0.5*self.bsize

            centroid_coordinates[i, 0] = y_f
            centroid_coordinates[i, 1] = x_f

        return centroid_coordinates

    def outlier_rejection(self, centroid_coordinates, epsilon, DBSCAN):
        dbscan = DBSCAN(eps=epsilon, min_samples=2)
        labels = dbscan.fit_predict(centroid_coordinates)

        cleaned_coordinates = centroid_coordinates[labels!=-1]
        return cleaned_coordinates

    def detect(self, raw_frame):
        self.frame_count = 0
        # if self.cap.isOpened():
        #     width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        #     height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # fourcc = cv2.VideoWriter.fourcc(*'XVID')
            # output = cv2.VideoWriter(output_path, fourcc, 1, (600, 600))
        frame = raw_frame
        frame = cv2.resize(frame, (self.frame_size, self.frame_size))

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

            if centroid_coordinates.size == 0:
                centroid_coordinates = self.pre_localize(test_preds)

            x_max = int(np.max(centroid_coordinates[:, 0]))
            x_min = int(np.min(centroid_coordinates[:, 0]))
            y_max = int(np.max(centroid_coordinates[:, 1]))
            y_min = int(np.min(centroid_coordinates[:, 1]))

            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            img_coords = ((x_max+x_min)/2, (y_max+y_min)/2)

            self.og_image_to_transmit = raw_frame
            self.image_to_transmit = frame
            self.img_coords = img_coords
            self.gps_position = gps_position
            self.uav_attitude = attitude

            # print(img_coords)

            # cv2.imshow("Frame", frame)
            # cv2.imwrite("", frame)

        self.frame_count += 1
        
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

if __name__ == "__main__":
    # vision_module = ClassifierDetect()
    # vision_module.detect()
    pass