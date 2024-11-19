import socket
import json
import os
import cv2
import numpy as np
import pickle
import struct
from pathlib import Path
from GlobalVars import *
from PIL import ImageGrab
import time

par_exit =1

def socket_lisener():
    # flag = 1
    global global_vars
    cnt = 0
    while global_vars.flag_socket_toggle:
        try:
            # global par_exit,client_socket_image,payload_size,data_img #,cap
            # Define the server's IP address and port
            server_ip = '0.0.0.0'  # Listen on all available network interfaces
            server_port = 8080  # Choose a port number

            # Create a socket to listen for incoming connections
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((server_ip, server_port))
            server_socket.listen()  # Listen for a single incoming connection

            print(f"Server is listening on {server_ip}:{server_port}")

            # Accept an incoming connection
            client_socket, client_address = server_socket.accept()
            print(f"Accepted connection from {client_address}")

            while global_vars.flag_socket_toggle:
                # Receive data from the client
                data = client_socket.recv(1024).decode()

                # Parse the JSON data
                json_data = json.loads(data)
                if not data:
                    # If no data is received, the client has disconnected
                    print("Client disconnected",par_exit)
                    break
                else:
                    message = "success"
                    client_socket.sendall(message.encode())
                if json_data['data'][1] == "out":
                    par_exit =0
                send_list = []
                info_received_decision = []
                info_received_decision = json_data["data"].split(",")

                if info_received_decision[0] == "TERMINATION":
                    response = "Terminating all threads"
                    client_socket.send(response.encode())
                    client_socket.close()
                    server_socket.close()
                    global_vars.termination_flag = 0
                    global_vars.flag_socket_toggle = 0

                elif info_received_decision[0] == "START":
                    if info_received_decision[1] == "YES":
                        response= "Starting all threads now"
                        client_socket.send(response.encode())
                        global_vars.start_all_threads = 1
                    else:
                        global_vars.start_all_threads = 0

                elif info_received_decision[0] == "VISION":
                    if info_received_decision[1] == "OFF":
                        response = "Vision module: OFF, success"
                        client_socket.send(response.encode())
                        global_vars.detection_process_flag = 0
                    else:
                        response = "Vision module: ON, success"
                        client_socket.send(response.encode())
                        global_vars.detection_process_flag = 1

                elif info_received_decision[0] == "IMG":
                    # frame = frame_to_transmit
                    img = ImageGrab.grab(bbox=(0, 40, 1280, 760))
                    img_np = np.array(img)
                    frame = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
                    frame = global_vars.frame_to_transmit
                    # cv2.imshow("T1", frame)
                    # cv2.waitKey(50)
                    # cv2.destroyAllWindows()
                    # Starting transmission to control board
                    print("Start transmission")
                    response = "ImageSend"
                    client_socket.send(response.encode())
                    frame = np.array(frame)
                    # frame = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
                    a = pickle.dumps(frame)
                    message = struct.pack("Q", len(a)) + a
                    client_socket.sendall(message)
                    print("finished")
                    
            # global_vars_all.flag = 0
        except:
            if global_vars.flag_socket_toggle:
                print("Something went wrong... Restarting")
                # Close the client socket and the server socket
                client_socket.close()
                server_socket.close()
            else:
                print("Overwritten ... Socket Listener: Off")
            # global_vars.flag = 1
    print("Connection to ground UI ends peacefully")

def socket_listener_main():
    global global_vars
    while global_vars.flag_socket_toggle:
        try:
            # global par_exit,client_socket_image,payload_size,data_img #,cap
            # Define the server's IP address and port
            server_ip = '0.0.0.0'  # Listen on all available network interfaces
            server_port = 8080  # Choose a port number

            # Create a socket to listen for incoming connections
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
            server_socket.bind((server_ip, server_port))
            server_socket.listen()  # Listen for a single incoming connection

            print(f"Server is listening on {server_ip}:{server_port}")

            # Accept an incoming connection
            client_socket, client_address = server_socket.accept()
            print(f"Accepted connection from {client_address}")

            while global_vars.flag_socket_toggle:
                # Receive data from the client
                data = client_socket.recv(1024).decode()

                # Parse the JSON data
                json_data = json.loads(data)
                if not data:
                    # If no data is received, the client has disconnected
                    print("Client disconnected",par_exit)
                    break
                else:
                    message = "success"
                    client_socket.sendall(message.encode())
                # Print the received JSON data
                print("Received JSON data:",json_data['data'])
                # print(json_data['name'])
                if json_data['data'][1] == "out":
                    par_exit =0
                send_list = []
                info_received_decision = []
                info_received_decision = json_data["data"].split(",")
                print(info_received_decision)
                # print(info_received_decision[0])
                # if info_received_decision[0] == "Information":
                #     single_msg = "Information_Requested,1,1,1,1,1,1,{},{},{},{},{},{},{}".format(str(global_vars.gps_uav_alt),str(global_vars.trigger_land_main),global_vars.mode,global_vars.option_reference,str(global_vars.start_cv_waypoint),str(global_vars.alt_land),str(global_vars.error_information))
                #     global_vars.error_information = "\n"
                #     print("Full message: ",single_msg)
                #     response = single_msg
                #     client_socket.send(response.encode())
                if info_received_decision[0] == "TERMINATION":
                    response = "Terminating all threads"
                    client_socket.send(response.encode())
                    client_socket.close()
                    server_socket.close()
                    global_vars.termination_flag = 0
                    global_vars.flag_socket_toggle = 0
                elif info_received_decision[0] == "START":
                    if info_received_decision[1] == "YES":
                        response= "Starting all threads now"
                        client_socket.send(response.encode())
                        global_vars.start_all_threads = 1
                    else:
                        global_vars.start_all_threads = 0
                elif info_received_decision[0] == "VISION":
                    if info_received_decision[1] == "OFF":
                        response = "Vision module: OFF, success"
                        client_socket.send(response.encode())
                        global_vars.detection_process_flag = 0
                    else:
                        response = "Vision module: ON, success"
                        client_socket.send(response.encode())
                        global_vars.detection_process_flag = 1
                # elif info_received_decision[0] == "TRIGGER":
                #     if info_received_decision[1] == 'ON':
                #         global_vars.detection_algorithm.flag_trigger = 1
                #         global_vars.detection_algorithm.auto_land = 0
                #         global_vars.mode = "MESSAGE ONLY"
                #         global_vars.stop_flag_global = 1
                #     elif info_received_decision[1] == 'OFF':
                #         global_vars.detection_algorithm.flag_trigger = 0
                #         global_vars.detection_algorithm.auto_land = 0
                #         global_vars.mode = "FORCE ABORT"
                #         global_vars.stop_flag_global = 0
                #     elif info_received_decision[1] == 'AUTO':
                #         global_vars.detection_algorithm.flag_trigger = 0
                #         global_vars.detection_algorithm.auto_land = 1
                #         global_vars.mode = "AUTO ABORT"
                #         global_vars.stop_flag_global = 1
                #     single_msg_full = global_vars.mode
                #     print("Full message: ", single_msg_full)
                #     # Process the data
                #     response = single_msg_full
                #     client_socket.send(response.encode())
                # elif info_received_decision[0] == "ALT":
                #     print(info_received_decision[1])
                #     single_msg_full = "ALT CHANGED"
                #     print("Full message: ",single_msg_full)
                #     # Process the data or send a response as needed
                #     global_vars.alt_land = int(info_received_decision[1])
                #     response = single_msg_full
                #     client_socket.send(response.encode())
                # elif info_received_decision[0] == "REF":
                #     global_vars.path_air_change = str(Path.home())+ "/Airports/" # linux operation /, windows \
                #     global_vars.dir_change = os.path.join(global_vars.path_air_change, info_received_decision[1])
                #     print(global_vars.dir_change)
                #     # further processes to change the images that we are refering to
                # elif info_received_decision[0] == "ADV_ST":
                #     if info_received_decision[1] != "E":
                #         global_vars.IP_SERVER = info_received_decision[1]
                #     if info_received_decision[2] != "E":
                #         global_vars.IP_JETSON = info_received_decision[2]
                #     if info_received_decision[3] != "E":
                #         global_vars.IP_PLATFORM = info_received_decision[3]
                #     if info_received_decision[4] != "E":
                #         global_vars.TRACK_LOOP_CNT = int(info_received_decision[4])
                #     if info_received_decision[5] != "E":
                #         global_vars.KALMAN_TRACK_CNT = int(info_received_decision[5])
                #     if info_received_decision[6] != "E":
                #         global_vars.DECISION_DISTANCE_IN_PIXELS = int(info_received_decision[6])
                #     if info_received_decision[7] != "E":
                #         global_vars.distance_threshold_kalman = int(info_received_decision[7])
                #     if info_received_decision[8] != "E":
                #         global_vars.PERSPECTIVE_POINT_OFFSET = int(info_received_decision[8])
                #     message = "Settings Imported"
                #     client_socket.sendall(message.encode())
                elif info_received_decision[0] == "IMG":
                    og_frame = global_vars.og_frame_to_transmit
                    frame = global_vars.frame_to_transmit
                    time.sleep(1)
                    # Starting transmission to control board
                    print("Start transmission")
                    response = "ImageSend"
                    client_socket.send(response.encode())
                    frame = np.array(frame)
                    og_frame = np.array(og_frame)

                    # img_coord = {
                    #     "x": global_vars.img_coords[0],
                    #     "y": global_vars.img_coords[1]
                    # }

                    # locationGPS = {
                    #     "LatDeg": global_vars.gps_position[0],
                    #     "LngDeg": global_vars.gps_position[1],
                    #     "AltM": global_vars.gps_position[2]
                    # }


                    # imgCoordString = json.dumps(img_coord)
                    # locationGPSString = json.dumps(locationGPS)

                    # frame = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
                    a = pickle.dumps(frame)
                    b = pickle.dumps(og_frame)
                    c = a+b

                    composite_frame = struct.pack("Q", len(c))+struct.pack("Q", len(a))+struct.pack("Q", len(b))+c

                    client_socket.sendall(composite_frame)
                    # message_frame = struct.pack("Q",len(a))+a
                    # message_og_frame = struct.pack("Q", len(b))+b
                    # client_socket.sendall(message_frame)
                    # client_socket.sendall(message_og_frame)
                    print("finished")

                elif info_received_decision[0] == "ImProc":
                    response = "Algorithm Selected: ImProc, success"
                    client_socket.send(response.encode())
                    global_vars.detector_model = 1

                elif info_received_decision[0] == "Classifier":
                    response = "Algorithm Selected: Classifier, success"
                    client_socket.send(response.encode())
                    global_vars.detector_model = 2

                elif info_received_decision[0] == "Yolo":
                    response = "Algorithm Selected: YOLOv8, success"
                    client_socket.send(response.encode())
                    global_vars.detector_model = 3

                    # cv2.waitKey(100)
                # elif info_received_decision[0] == "DEC":
                #     response = global_vars.dec
                #     client_socket.send(response.encode())
        except Exception as error:
            if global_vars.flag_socket_toggle:
                print("Something went wrong... Socket Restarting: ", error)
                # Close the client socket and the server socket
                client_socket.close()
                server_socket.close()
            else:
                print("Overwritten ... Socket Listener: Off")
            # global_vars.flag = 1
    print("Connection to ground UI ends peacefully")