import socket
import json
import numpy as np
import pickle
import struct
from GlobalVars import *
import time


def encode_numpy(obj):
    if isinstance(obj, np.ndarray):
        # Convert NumPy array to dictionary with metadata
        return {
            "__ndarray__": True,
            "data": obj.tobytes(),
            "dtype": str(obj.dtype),
            "shape": obj.shape,
        }
    raise TypeError(f"Type {type(obj)} is not serializable")

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
                    par_exit = 0

                info_received_decision = []
                info_received_decision = json_data["data"].split(",")
                print(info_received_decision)

                if info_received_decision[0] == "TERMINATION":
                    response = "Terminating all threads"
                    client_socket.send(response.encode())
                    client_socket.close()
                    server_socket.close()
                    global_vars.termination_flag = 0
                    global_vars.flag_socket_toggle = 0
                    global_vars.hub_connection.stop()

                elif info_received_decision[0] == "INITIALIZE":
                    if info_received_decision[1] == "YES":
                        response = "Starting all threads now"
                        client_socket.send(response.encode())
                        # global_vars.start_all_threads = 1
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
                        global_vars.start_all_threads = 1
                        global_vars.detection_process_flag = 1
                        
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

                elif info_received_decision[0] == "IMG":
                    # print("Image Request Received!")
                    response = "ImageSend"
                    client_socket.send(response.encode())
                    time.sleep(1)
                    # Starting transmission to control board
                    if global_vars.og_image_to_transmit.size > 0 and global_vars.image_to_transmit.size > 0 :
                        response = "ImgAvail"
                        client_socket.send(response.encode())

                        og_frame = global_vars.og_image_to_transmit
                        frame = global_vars.image_to_transmit

                        frame = np.array(frame)
                        og_frame = np.array(og_frame)

                        frame_stream = pickle.dumps(frame)
                        og_frame_stream = pickle.dumps(og_frame)
                        img_coords_stream = pickle.dumps(global_vars.img_coords)
                        gps_pos_stream = pickle.dumps(global_vars.gps_position)
                        attitude_stream = pickle.dumps(global_vars.uav_attitude)

                        data_stream = frame_stream+og_frame_stream+img_coords_stream+gps_pos_stream+attitude_stream
                        stream_len = len(data_stream)
                        frame_stream_len = len(frame_stream)
                        og_frame_stream_len = len(og_frame_stream)
                        coords_stream_len = len(img_coords_stream)
                        gps_stream_len = len(gps_pos_stream)
                        attitude_stream_len = len(attitude_stream)

                        stream_len = struct.pack("Q", stream_len)
                        frame_stream_len = struct.pack("Q", frame_stream_len)
                        og_frame_stream_len = struct.pack("Q", og_frame_stream_len)
                        coords_stream_len = struct.pack("Q", coords_stream_len)
                        gps_stream_len = struct.pack("Q", gps_stream_len)
                        attitude_stream_len = struct.pack("Q", attitude_stream_len)

                        data_header = stream_len+frame_stream_len+og_frame_stream_len+coords_stream_len+gps_stream_len+attitude_stream_len

                        client_socket.sendall(data_header)
                        # print("Data header sent")

                        client_socket.sendall(data_stream)
                        # print("Data stream sent")

                    else:
                        response = "Images not generated yet!\n"
                        client_socket.send(response.encode())
                        print("No generated images to transmit!")

        except Exception as error:
            if global_vars.flag_socket_toggle:
                print("Something went wrong... Socket Restarting: ", error)
                # Close the client socket and the server socket
                client_socket.close()
                server_socket.close()
            else:
                print("Overwritten ... Socket Listener: Off")
    print("Connection to ground UI ends peacefully")