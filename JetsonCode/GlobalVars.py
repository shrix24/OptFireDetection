class Globals():
    def __init__(self):
        self.gps_uav_alt = 0

        self.width = 1920
        self.height = 1080
        self.flag_socket_toggle = 1
        self.detection_thread_flag = 1
        self.flag_init_video_server = 1
        self.corrupt_frames = 0
        self.video_server_main_thread_flag = 1
        self.read_frames = 1 # 
        self.detection_process_flag = 1 # flag that is specifying that the system is ON or OFF (Detection)
        self.termination_flag = 1
        self.start_all_threads = 0
        self.detector_model = 0
        # Error information variables
        self.error_information = "\n"
        self.seperator = "\n"
        # IP for video server and jetson IP address
        self.IP_SERVER = "http://127.0.0.1:8008"
        self.IP_JETSON = "192.168.134.242"
        self.IP_PLATFORM = "http://127.0.0.1:5000"
    
    def update(self,var):
        self.alt_land = var

global_vars = Globals()