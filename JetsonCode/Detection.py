from Classifier_main import Classifier_Detect
from ImProc_Detect_main import ImProc_Detect
from Yolo_main import YOLO_Detect
from GlobalVars import global_vars

class Detector:
    def __init__(self, algorithm_choice) -> None:
        self.algorithm_choice = algorithm_choice

    def main_detect(self):
        if self.algorithm_choice == 1:
            self.vision_module = ImProc_Detect()
            self.vision_module.detect()
            self.og_image_to_transmit = self.vision_module.og_image_to_transmit
            self.image_to_transmit = self.vision_module.image_to_transmit
        elif self.algorithm_choice == 2:
            self.vision_module = Classifier_Detect()
            self.vision_module.detect()
            self.og_image_to_transmit = self.vision_module.og_image_to_transmit
            self.image_to_transmit = self.vision_module.image_to_transmit
        elif self.algorithm_choice == 3:
            self.vision_module = YOLO_Detect()
            self.vision_module.detect()
            self.og_image_to_transmit = self.vision_module.og_image_to_transmit
            self.image_to_transmit = self.vision_module.image_to_transmit

if __name__ == "__main__":
    pass