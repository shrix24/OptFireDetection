import numpy as np
import cv2
from ultralytics import YOLO


class YOLO_Detect:
    def __init__(self) -> None:
        # self.video_path = r"C:\Users\Aditya Shrikhande\Downloads\15184524-uhd_3840_2160_24fps.mp4"
        self.model = YOLO(r"C:\development\XPrizev3\yolov8s\new_model.pt")

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