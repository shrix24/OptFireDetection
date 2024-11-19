import requests
import socket
from GlobalVars import global_vars
import subprocess as sp
import shlex
import numpy as np
import  cv2
from ImProc_Detect_main import ImProc_Detect
from Classifier_main import Classifier_Detect
from Yolo_main import YOLO_Detect
import time
from Detection import Detector

class VideoServer_functions():
    def __init__(self,server_ip,host_ip):
        self.IP_VIDEO = server_ip
        self.VIDEO_URL_startStream = self.IP_VIDEO+"/core/Streams/startOrJoinStream"
        self.HOST_IP = host_ip
        self.VIDEO_URL_stopStream = self.IP_VIDEO+"/core/Streams/stopOrLeaveStream"
    
    def get_video_source(self):
        # VIDEO_URL = "http://11.1.1.1:8008"
        print("Getting Available Ids...")
        response = requests.get(self.IP_VIDEO + '/core/Sources/getAvailableSources')
        video_response = response.json()[0]
        self.video_id = video_response["id"]
        # return video_id
    
    def close_video_stream(self):
        requestURL = self.IP_VIDEO+"/core/Streams/getActiveStreams"
        response = requests.post(requestURL)
        video_response = response.json()[0]
        self.video_id = video_response["id"]
        if self.video_id != []:
            data = {
            "streamId": self.video_id,
            "ip": self.HOST_IP
            }
            response = requests.post(self.VIDEO_URL_stopStream, json=data)
            # stopURL = self.VIDEO_URL_stopStream + video_id
            # stopURL = "http://11.1.1.1:8008/core/Streams/stopStream?streamId="+video_id
            # response = requests.post(stopURL)
            print(response)

    def start_video_stream(self):
        hostname=socket.gethostname()
        # IPAddr="11.40.56.216"
        # VIDEO_URL = "http://11.1.1.1:8008/core/Streams/startStream"
        data = {
        "sourceId": self.video_id,
        "resolution": {
            "widthPixels": 1920,
            "heightPixels": 1080
        },
        "frameRate": 30,
        "bitrateKbps": 8192,
        "targetIp": self.HOST_IP
        }
        response = requests.post(self.VIDEO_URL_startStream, json=data)
        target_address = response.json()["targetIps"]
        connection_client = response.json()["clientConnectionAddresses"]
        i = 0
        for target_add in target_address:
            if target_add == self.HOST_IP:
                break
            i = i + 1
        client_conn = connection_client[i]
        print(client_conn)
        x = client_conn.split("//")
        ip_port = x[1].split(":")
        print(ip_port)
        self.IP_SDP = ip_port[0]
        self.PORT_SDP = ip_port[1]
        # return ip_port[0],ip_port[1]

    def generate_sdp_file(self):
        with open("test_2.sdp","r+")as fp:
            fp.truncate(0)
        fp.close()
        f = open("test_2.sdp", "a")
        # stuff_in_string = "v=0\no=- 0 0 IN IP4 127.0.0.1\ns= No Name\nt=0 0\na=tool:libavformat 60.4.101\nc=IN IP4 {}\nm=video {} RTP/AVP 96\nb=AS:10000\na=rtpmap:96 H264/90000\na=fmtp:96 packetization".format(self.IP_SDP,self.PORT_SDP)
        stuff_in_string = "c=IN IP4 {}\nm=video {} RTP/AVP 96\na=rtpmap:96 H264/90000".format(self.IP_SDP,self.PORT_SDP)

        f.write(stuff_in_string)
        f.close()
    
    def start_connection_with_server(self):
        self.get_video_source()
        self.start_video_stream()
        self.generate_sdp_file()

# Video  Initiation Sequence for feed connection
def video_server_connection_thread():
    global video_server, global_vars
    # while global_vars.restart_thread_video_derver:
    try:
        # ip_server = "http://127.0.0.1:5000"
        ip_server = global_vars.IP_SERVER
        # ip_host = "192.168.134.242" # The two varibales need to be derived by the user (Control UI), This is the XAVIER IP
        ip_host = global_vars.IP_JETSON # The two varibales need to be derived by the user (Control UI), This is the XAVIER IP
        global_vars.video_server = VideoServer_functions(ip_server,ip_host)
        # This will start the server, connect, and generate the sdp file
        global_vars.video_server.start_connection_with_server()
        print("Connected to Video Server!")
        # restart_thread_video_derver = 0
        width = 1920  # Use low resolution (for testing).
        height = 1080
        # ffmpeg_cmd = shlex.split(f'ffmpeg -hide_banner -loglevel panic -nostats -nostdin -probesize 32 -flags low_delay -fflags nobuffer -protocol_whitelist file,udp,rtp -i /home/da/X-Plane-ULTRA-Simulation/Scripts/test_2.sdp -pix_fmt bgr24 -an -vsync 2 -b:v 2000k -preset slower -vcodec rawvideo -f rawvideo pipe:')
        # ffmpeg_cmd = shlex.split(f'ffmpeg -hide_banner -loglevel panic -nostats -nostdin -probesize 32 -flags low_delay -fflags nobuffer -protocol_whitelist file,udp,rtp -i /home/da/X-Plane-ULTRA-Simulation/Scripts/test_2.sdp -pix_fmt bgr24 -an -vsync 2 -vf v360=input=sg:ih_fov=120:iv_fov=67.5:output=flat:d_fov=105:w=1920:h=1080 -b:v 2000k -preset slower -vcodec rawvideo -f rawvideo pipe:')
        ffmpeg_cmd = shlex.split(f'ffmpeg -hide_banner -loglevel panic -nostats -nostdin -probesize 32 -flags low_delay -fflags nobuffer -protocol_whitelist file,udp,rtp -i test_2.sdp -pix_fmt bgr24 -an -vsync 2 -c:v libc264 -b:v 1000k -preset slower -crf 18 -r 30 rawvideo -f rawvideo pipe:')
        # Open sub-process that gets in_stream as input and uses stdout as an output PIPE.
        global_vars.process = sp.Popen(ffmpeg_cmd, stdout=sp.PIPE) #,stderr=sp.DEVNULL
    except Exception as error:
        print("Something went wrong: Init Video Server... Re-try") # if error occur restart the process that is assigned to
        global_vars.error_information += "Something went wrong: Init Video Server... Re-try"+global_vars.seperator
        global_vars.video_server.close_video_stream()
        restart_thread_video_derver = 1

def video_server_main_thread():
    global global_vars
    width = 1920  # Use low resolution (for testing).
    height = 1080

    vision_module = Detector(global_vars.detector_model)

    while global_vars.video_server_main_thread_flag:
        try:
            if global_vars.flag_init_video_server:
                video_server_connection_thread()
                global_vars.flag_init_video_server = 0
                
            #### Adding here the detection part as: Video to a different thread has a BIG latency ####
            print("Getting frames")
            raw_frame = global_vars.process.stdout.read(width*height*3)
            print(len(raw_frame))

            frame = np.frombuffer(raw_frame, np.uint8)
            image = frame.reshape((global_vars.height, global_vars.width,3))
            global_vars.frame_to_transmit = image

            if len(raw_frame) != (width*height*3):
                pass
            else:
                if global_vars.detection_process_flag == 1:
                    vision_module.main_detect(image)
                    global_vars.og_image_to_transmit = vision_module.og_image_to_transmit
                    global_vars.image_to_transmit = vision_module.image_to_transmit
                    global_vars.img_coords = vision_module.img_coords
                    global_vars.gps_position = vision_module.gps_position
                    global_vars.attitude = vision_module.attitude

        except Exception as error:
            print("Something went wrong: Video Server... Restarting", error)
            global_vars.error_information += "Something went wrong: Video Server... Restarting"+global_vars.seperator
            global_vars.flag_init_video_server = 1
    global_vars.video_server.close_video_stream()
    print("Video Server Connection end peacfully")
