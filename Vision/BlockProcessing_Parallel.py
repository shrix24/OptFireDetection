import cv2
import joblib
import numpy as np
from skimage.util import view_as_blocks
from WaveletTraining import Window_Wavelet_Features
from sklearn.cluster import DBSCAN
from coordinate_converter import Image2World
# from multiprocessing import Pool
# from joblib import Parallel, delayed


# def parallel_classify(frame_blocks, i, j):
#     test_preds = np.ones((int(frame_size/bsize), int(frame_size/bsize)))

#     args = [(i, j, frame_blocks) for i in range(frame_blocks.shape[0]) for j in range(frame_blocks.shape[1])]

#     with Pool() as pool:
#         output = pool.map(classify, args)

def classify(block, LGBM_Model):
    img_features = Window_Wavelet_Features(block).feature_extract_infer(block)
    test_features = np.expand_dims(img_features, axis=0)
    test_for_RF = np.reshape(test_features, (1, -1))
    test_prediction = LGBM_Model.predict(test_for_RF)
    test_prob = LGBM_Model.predict_proba(test_for_RF)

    if test_prediction == 0 and test_prob[0][0] >= 0.85:
        return test_prediction
    else:
        return

def pre_localize(test_preds):
    idx = np.where(test_preds==0)
    zero_idx = list(zip(idx[0], idx[1]))
    zero_idx = np.array(zero_idx)
    centroid_coordinates = np.zeros(zero_idx.shape)

    for i in range(zero_idx.shape[0]):
        if zero_idx[i, 0] == 0:
            x_f = 0 + 0.5*bsize
        else:
            x_f = 0 + zero_idx[i, 0]*bsize + 0.5*bsize

        if zero_idx[i, 1] == 0:
            y_f = 0 + 0.5*bsize
        else:
            y_f = 0 + zero_idx[i, 1]*bsize + 0.5*bsize

        centroid_coordinates[i, 0] = y_f
        centroid_coordinates[i, 1] = x_f

    return centroid_coordinates

# def clustering(centroid_coordinates, epsilon, DBSCAN):
#     dbscan = DBSCAN(eps=epsilon, min_samples=2)
#     clusters = dbscan.fit_predict(centroid_coordinates)

#     return clusters

def outlier_rejection(centroid_coordinates, epsilon, DBSCAN):
    dbscan = DBSCAN(eps=epsilon, min_samples=2)
    labels = dbscan.fit_predict(centroid_coordinates)

    cleaned_coordinates = centroid_coordinates[labels!=-1]
    return cleaned_coordinates

if __name__ == "__main__":
    LGBM_Model = joblib.load(r"C:\development\XPrizev2\LGBM_Wavelet_Parameters")
    video_path = r"C:\Users\Aditya Shrikhande\Downloads\15184522-uhd_3840_2160_24fps.mp4"
    output_path = r"C:\development\XPrizev2\OpticalSmokeDetections_bbox4.avi"
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    frame_size = 600
    bsize = 60

    intrinsic_params = [50, 25, 0, 400, 400]
    extrinsic_params = [1.23, 0, -0.51, 0, -54.7]
    vehicle_pose = [53.3817, -1.4802, 300, 0, 2.2, 0]

    coords = Image2World(intrinsic_params, extrinsic_params, vehicle_pose)

    if cap.isOpened():
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter.fourcc(*'XVID')
    output = cv2.VideoWriter(output_path, fourcc, 1, (600, 600))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (frame_size, frame_size))

        if frame_count%24 == 0 or frame_count == 0:
            frame_blocks = view_as_blocks(frame, (bsize, bsize, 3))
            test_preds = np.ones((int(frame_size/bsize), int(frame_size/bsize)))

            for i in range(frame_blocks.shape[0]):
                for j in range(frame_blocks.shape[1]):
                    block = frame_blocks[i, j, 0]
                    test_preds[i, j] = classify(block, LGBM_Model)
                    if test_preds[i, j] == 0:
                        x_min = j*bsize
                        y_min = i*bsize
                        w = bsize
                        h = bsize
                        # cv2.rectangle(frame, (x_min, y_min), (x_min+w, y_min+h), (0, 255, 0), 2)

            centroid_coordinates = pre_localize(test_preds)
            centroid_coordinates = outlier_rejection(centroid_coordinates, bsize, DBSCAN)

            if centroid_coordinates.size == 0:
                centroid_coordinates = pre_localize(test_preds)

            x_max = int(np.max(centroid_coordinates[:, 0]))
            x_min = int(np.min(centroid_coordinates[:, 0]))
            y_max = int(np.max(centroid_coordinates[:, 1]))
            y_min = int(np.min(centroid_coordinates[:, 1]))

            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            # img_coords = ((x_max+x_min)/2, (y_max+y_min)/2)
            # coord_vector = coords.Convert(img_coords)
            # print(coord_vector)
            cv2.imshow("Frame", frame)
            output.write(frame)

        frame_count += 1
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    
    output.release()
    cap.release()
    cv2.destroyAllWindows()