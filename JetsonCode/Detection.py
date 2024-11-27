from Classifier_main import Classifier_Detect
from ImProc_Detect_main import ImProc_Detect
from Yolo_main import YOLO_Detect
from GlobalVars import global_vars

class Detector:
    def __init__(self, algorithm_choice) -> None:
        self.algorithm_choice = algorithm_choice

    def main_detect(self, raw_frame):
        # print("Performing Detection")
        if self.algorithm_choice == 1:
            # print("ImProc Detector Model")
            self.vision_module = ImProc_Detect()
            # print("Model Initialised")
            self.vision_module.detect(raw_frame)

        elif self.algorithm_choice == 2:
            # print("Classifier Detector Model")
            self.vision_module = Classifier_Detect()
            self.vision_module.detect(raw_frame)

        elif self.algorithm_choice == 3:
            # print("Yolov8 Detector Model")
            self.vision_module = YOLO_Detect()
            self.vision_module.detect(raw_frame)

if __name__ == "__main__":
    pass