## Structure for the new version with multiple threading ##
# -> Main Thread -> Switch on/off other threads
# -> Computer Vision Thread -> On/Off/Restart on error, Computer Vision processes -> Runway Detection/ Fire Detection (Future)
# -> Platform Control Thread -> Send/ Receive messages, Auto restart
# -> Video Thread -> Connect to Video Server, Restart connection on error
from VideoServer import *
from SocketTesting import *
import threading
# from DA_DataTransfer import *
from GlobalVars import *
import time


def manager():
    #switch on/off subsequences
    global global_vars
    print("This is the manager thread and is ON")
    global_vars.error_information += "This is the manager thread and is ON"+global_vars.seperator
    while global_vars.termination_flag:
        time.sleep(1)
        # print("hello")
    # Switch off the detection part
    global_vars.detection_thread_flag = 0
    global_vars.video_server_main_thread_flag = 0
    global_vars.read_frames = 0
    # cv2.destroyAllWindows()


# if __name__ == '__main__':
# Create a thread
thread_manager = threading.Thread(target=manager)

# Start the socket listener thread
# thread_detection = threading.Thread(target=main_detect)
thread_socket_listener = threading.Thread(target=socket_listener_main)

thread_manager.start()
thread_socket_listener.start()

while not global_vars.start_all_threads:
    time.sleep(1)

thread_video_server = threading.Thread(target=video_server_main_thread)

while not global_vars.flag_init_video_server:
    time.sleep(1)

while global_vars.detection_process_flag == 0:
    time.sleep(1)

thread_video_server.start()