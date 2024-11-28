import customtkinter
from tkinter import *
from tkinter import messagebox
import threading
from PIL import Image, ImageFile, ImageTk
from datetime import datetime
import sys
import smtplib
import ssl
from email.message import EmailMessage
import tkinter.messagebox as tkmb
import os
from tkinter import filedialog
from datetime import date
import socket
import json
import cv2
import pickle
import struct
import numpy as np
import time
from coord_converter_v4 import Image2World

ImageFile.LOAD_TRUNCATED_IMAGES = True


# Define email sender and receiver
email_sender = 'noreplyflight@gmail.com'
email_password = 'rzlpwsujlhlfoupf'
email_receiver = ['a.m.shrikhande@sheffield.ac.uk']
payload_size = struct.calcsize('Q')
img_rec = 0
today = date.today()
date_today = today.strftime("%d%m%y")
main_path_images = r"C:\FireSheffield"
folder_images = r"C:\FireSheffield\FireSystem" + date_today

if not os.path.exists(folder_images):
    os.mkdir(folder_images)

folder_images_detection = folder_images + r"\detection"
folder_images_original = folder_images + r"\original"

if not os.path.exists(folder_images_detection):
    os.mkdir(folder_images_detection)
if not os.path.exists(folder_images_original):
    os.mkdir(folder_images_original)

# print(folder_images,folder_images_detection,folder_images_original)
counter_images = 0

def resource_path2(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class LoginUIFirst(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        # self.attributes('-fullscreen', True)
        # self.state('zoomed')
        self.username = ""
        self.password = ""
        self.title("Fire Detection System Control")
        self.geometry(f"{380}x{300}")
        # customtkinter.CTkFrame(self, width=140, corner_radius=0)
        label = customtkinter.CTkLabel(self, text="Welcome to Fire Detection System Control Panel")

        label.pack(pady=10)

        frame = customtkinter.CTkFrame(master=self)
        frame.pack(pady=20, padx=40, fill='both', expand=True)

        label = customtkinter.CTkLabel(master=frame, text='Fire Detection System Control Panel')
        label.pack(pady=12, padx=10)

        self.user_entry = customtkinter.CTkEntry(master=frame, placeholder_text="Username")
        self.user_entry.pack(pady=12, padx=10)

        self.user_pass = customtkinter.CTkEntry(master=frame, placeholder_text="Password", show="*")
        self.user_pass.pack(pady=12, padx=10)

        button = customtkinter.CTkButton(master=frame, text='Login', command=self.login)
        button.pack(pady=12, padx=10)

    # def update(self):
    #     app.after(1000, clock)

    def login(self):
        if self.user_entry.get() == self.username and self.user_pass.get() == self.password:
            tkmb.showinfo(title="Login Successful", message="You have logged in Successfully")
            self.quit()  # Quiting and destroy window to proceed
            self.destroy()
            self.app = FireControlPanel()
            # setting attribute
            # run first time
            self.app.start_update_function()
            self.app.mainloop()

        elif self.user_entry.get() == self.username and self.user_pass.get() != self.password:
            tkmb.showwarning(title='Wrong password', message='Please check your password')
        elif self.user_entry.get() != self.username and self.user_pass.get() == self.password:
            tkmb.showwarning(title='Wrong username', message='Please check your username')
        else:
            tkmb.showerror(title="Login Failed", message="Invalid Username and password")

class FireControlPanel(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        ### Variables for information panel
        self.start_update = 0
        self.reconnect_to_board = 0
        self.camera_res = (1920, 1080)
        self.FoV = (140, 110)

        # # Initialize the task queue and worker thread
        # self.task_queue = queue.Queue()
        # self.worker_thread = threading.Thread(target=self.worker_function, daemon=True)
        # self.worker_thread.start()

        self.resized_up = np.array([])
        self.resized_up_og = np.array([])

        # Create a fullscreen window
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()

        # configure window
        my_font = customtkinter.CTkFont(family="Italic", size=25)
        my_font_c = customtkinter.CTkFont(family="Italic", size=18)
        self.title("Control Panel")
        self.geometry("%dx%d+0+0" % (int(self.screen_width), int(self.screen_height)))

        # configure grid layout (4x4)
        self.grid_columnconfigure(0, weight=300)
        self.grid_rowconfigure(0, weight=300)

        # Derived image frame, image will be showed on this frame after derivation
        # Main Frame for the UI
        self.scrollable_frame_main = customtkinter.CTkFrame(self, fg_color="#242424")
        self.scrollable_frame_main.grid_columnconfigure(0, weight=1)
        self.scrollable_frame_main.grid_columnconfigure(1, weight=1)
        self.scrollable_frame_main.grid_rowconfigure(2, weight=1)
        self.scrollable_frame_main.grid(row=0, column=0, padx=(0, 0), pady=(0, 0), sticky="nsew")

        # Adding Logo Image at the top left part of the frame
        imgLogo = Image.open(resource_path2(r"C:\Users\Aditya Shrikhande\Downloads\logo_1.jpg"))
        # let's upscale the image using new  width and height
        up_width = int(self.screen_width/2)
        up_height = int(self.screen_height/2+self.screen_height/8)
        up_points = (up_width, up_height)
        imgLogo_1 = imgLogo.resize(up_points)
        w, h = imgLogo_1.size
        self.bg_imageLogos = customtkinter.CTkImage(imgLogo_1, size=(w, h))
        self.Thermal_Image_Label = customtkinter.CTkLabel(self.scrollable_frame_main, text="Processed Image",
                                                          image=self.bg_imageLogos, bg_color="#242424")
        self.Thermal_Image_Label.grid(row=0, column=1, padx=(5, 0), pady=(0, 0), sticky="nsew", rowspan=2)
        self.Original_Image_Label = customtkinter.CTkLabel(self.scrollable_frame_main, text="Original Image",
                                                          image=self.bg_imageLogos, bg_color="#242424")
        self.Original_Image_Label.grid(row=0, column=0, padx=(10, 5), pady=(0, 0), sticky="nsew", rowspan=2)

        # Tab for displaying system output
        self.tabview_sysout = customtkinter.CTkTabview(self.scrollable_frame_main, width=1)
        self.tabview_sysout.grid(row=2, column=0, padx=(10, 0), pady=(20, 20), sticky="nsew")
        self.tab_output = "System Output"
        self.tabview_sysout.add(self.tab_output)
        self.tabview_sysout.grid_rowconfigure(0, weight=1)
        self.tabview_sysout.grid_rowconfigure(1, weight=0)
        self.tabview_sysout.grid_rowconfigure(2, weight=1)
        self.tabview_sysout.grid_rowconfigure(3, weight=1)
        self.tabview_sysout.grid_rowconfigure(4, weight=1)

        # Keyframe Capture Button
        self.keyframe_capture_label = customtkinter.CTkLabel(self.tabview_sysout.tab(self.tab_output), text="Keyframe Capture")
        self.keyframe_capture_label.grid(row=0, column=0, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.keyframe_capture = customtkinter.CTkButton(self.tabview_sysout.tab(self.tab_output), 140, 28, command=self.capture_keyframe, text="Capture Keyframe")
        self.keyframe_capture.grid(row=1, column=0, padx=(10, 10), pady=(10, 10))
        self.keyframe_counter = 0

        # Coordinate Output Section
        self.appearance_mode_label = customtkinter.CTkLabel(self.tabview_sysout.tab(self.tab_output),
                                                            text="Image Coordinates")
        self.appearance_mode_label.grid(row=0, column=2, padx=(10, 10), pady=(5, 5), sticky="nsew")
        self.text_box_X = customtkinter.CTkEntry(self.tabview_sysout.tab(self.tab_output), width=140, height=15, bg_color="#242424", text_color="#FFFFFF")
        self.text_box_X.grid(row=1,column=2, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.text_box_Y = customtkinter.CTkEntry(self.tabview_sysout.tab(self.tab_output), width=140, height=15, bg_color="#242424", text_color="#FFFFFF")
        self.text_box_Y.grid(row=2, column=2, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.text_label_X = customtkinter.CTkLabel(self.tabview_sysout.tab(self.tab_output), text="X:")
        self.text_label_X.grid(row=1, column=1, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.text_label_Y = customtkinter.CTkLabel(self.tabview_sysout.tab(self.tab_output), text="Y:")
        self.text_label_Y.grid(row=2, column=1, padx=(10, 10), pady=(10, 10), sticky="nsew")

        # GPS Coordinate Output Section
        self.label_gps_coords = customtkinter.CTkLabel(self.tabview_sysout.tab(self.tab_output), text="GPS Coordinates")
        self.label_gps_coords.grid(row=0, column=4, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.text_box_lat = customtkinter.CTkEntry(self.tabview_sysout.tab(self.tab_output), width=140, height=15, bg_color="#242424", text_color="#FFFFFF")
        self.text_box_lat.grid(row=1, column=4, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.text_box_lon = customtkinter.CTkEntry(self.tabview_sysout.tab(self.tab_output), width=140, height=15, bg_color="#242424", text_color="#FFFFFF")
        self.text_box_lon.grid(row=2, column=4, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.lat_label = customtkinter.CTkLabel(self.tabview_sysout.tab(self.tab_output), text="Latitude:")
        self.lat_label.grid(row=1, column=3, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.lon_label = customtkinter.CTkLabel(self.tabview_sysout.tab(self.tab_output), text="Longitude:")
        self.lon_label.grid(row=2, column=3, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.gps_convert_button = customtkinter.CTkButton(self.tabview_sysout.tab(self.tab_output), 140, 28, command=self.obtain_gps, text="Obtain GPS Coordinates")
        self.gps_convert_button.grid(row=3, column=2, padx=(10, 10), pady=(1, 1), sticky="nsew")
        self.gps_send_button = customtkinter.CTkButton(self.tabview_sysout.tab(self.tab_output), 140, 28, command=self.coordinates, text="Send via email")
        self.gps_send_button.grid(row=3, column=4, padx=(10, 10), pady=(1, 1), sticky="nsew")
        self.gps_broadcast_button = customtkinter.CTkButton(self.tabview_sysout.tab(self.tab_output), 140, 28, command=self.coordinates, state="disabled", text="Broadcast to Swarm")
        self.gps_broadcast_button.grid(row=4, column=4, padx=(10, 10), pady=(1, 1), sticky="nsew")

        # Configuring System Connection and Toggle Tabs
        self.tabview = customtkinter.CTkTabview(self.scrollable_frame_main, width=1)
        self.tabview.grid(row=2, column=1, padx=(20, 20), pady=(20, 20), sticky="nsew", rowspan=2)
        self.tab_connection = "Connection"
        self.tab_toggle = "Toggle Threads"
        self.tabview.add(self.tab_connection)
        self.tabview.add(self.tab_toggle)
        self.tabview.tab(self.tab_toggle).grid_columnconfigure(0, weight=1)  # configure grid of individual tabs
        self.tabview.tab(self.tab_toggle).grid_columnconfigure(1, weight=1)
        self.tabview.tab(self.tab_toggle).grid_columnconfigure(2, weight=1)

        # Establish connection with the main server that is on board
        self.label_connection = customtkinter.CTkLabel(master=self.tabview.tab(self.tab_connection), text="Establish connection with the server:")
        self.label_connection.grid(row=0, column=0, columnspan=1, padx=10, pady=10, sticky="")
        self.switch_connection_var = customtkinter.StringVar(value="off")
        self.switch_connection = customtkinter.CTkSwitch(self.tabview.tab(self.tab_connection),
                                                  text="Connect to plane",
                                                  variable=self.switch_connection_var, onvalue="on", command=self.connection_command,
                                                  offvalue="off")
        self.switch_connection.grid(row=0, column=1, pady=10, padx=20, sticky=W)
        self.connection_label_arm = customtkinter.CTkButton(self.tabview.tab(self.tab_connection), text="Not Connected",
                                                                 font=my_font,
                                                                 fg_color="red", border_width=4,
                                                                 text_color=("gray10", "#DCE4EE"), state="disabled")
        self.connection_label_arm.grid(row=1, column=1, padx=(10, 20), pady=(10, 0), rowspan=1, sticky='W')
        self.entry_ip = customtkinter.CTkEntry(self.tabview.tab(self.tab_connection), placeholder_text="Connection IP")
        self.entry_ip.grid(row=1, column=0, columnspan=1, padx=20, pady=20, sticky="nsew")
        self.entry_port = customtkinter.CTkEntry(self.tabview.tab(self.tab_connection), placeholder_text="Connection Port")
        self.entry_port.grid(row=2, column=0, columnspan=1, padx=20, pady=20, sticky="nsew")


        # Prepare System Toggle Tab
        self.algorithm_label = customtkinter.CTkLabel(self.tabview.tab(self.tab_toggle), text="Choose an algorithm")
        self.algorithm_label.grid(row=0, column=0)
        self.algorithm_choice = customtkinter.IntVar(self.tabview.tab(self.tab_toggle), value=0)
        self.algorithm_radio_1 = customtkinter.CTkRadioButton(self.tabview.tab(self.tab_toggle), variable=self.algorithm_choice,
                                                              value=1, text="Image Processor")
        self.algorithm_radio_1.grid(row=1, column=0, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.algorithm_radio_2 = customtkinter.CTkRadioButton(self.tabview.tab(self.tab_toggle), variable=self.algorithm_choice,
                                                              value=2, text="Classifier")
        self.algorithm_radio_2.grid(row=2, column=0, sticky="nsew", padx=(10, 10), pady=(10, 10))
        self.algorithm_radio_3 = customtkinter.CTkRadioButton(self.tabview.tab(self.tab_toggle), variable=self.algorithm_choice,
                                                              value=3, text="Yolov8")
        self.algorithm_radio_3.grid(row=3, column=0, sticky="nsew", padx=(10, 10), pady=(10, 10))

        self.switch_all_var = customtkinter.StringVar(value="off")
        self.switch_all = customtkinter.CTkSwitch(self.tabview.tab(self.tab_toggle),
                                                             text="Toggle All Threads",
                                                             variable=self.switch_all_var, onvalue="on", command=self.toggle_all,
                                                             offvalue="off")
        self.switch_all.grid(row=0, column=1, pady=10, padx=20,sticky = "W")
        self.confirmation_button = customtkinter.CTkButton(self.tabview.tab(self.tab_toggle), 140, 28, text="Confirm Algorithm", 
                                                          font=my_font, border_width=4, command=self.confirm_algorithm)
        self.confirmation_button.grid(row=1, column=1, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.start_command = customtkinter.IntVar(value=0)
        self.start_button = customtkinter.CTkButton(self.tabview.tab(self.tab_toggle), 140, 28, text="Start", font=my_font,
                                                        border_width=4, command=self.send_start_command)
        self.start_button.grid(row=2, column=1, padx=(10, 10), pady=(10, 10),sticky = 'nsew')
        self.arm_system_label = customtkinter.CTkButton(self.tabview.tab(self.tab_toggle), 140, 28, text="Disarmed", font=my_font,
                                                     fg_color="red", border_width=4, state="disabled")
        self.arm_system_label.grid(row=3, column=1, padx=(10, 10), pady=(10, 10), sticky="nsew")

    # def sendOnBoard(self):
    #     # Convert the dictionary to a JSON string
    #     json_data = json.dumps(self.payload)
    #     # Send the message to the server
    #     self.client_socket.send(json_data.encode())
    #     # print("\nData sent to server successfully")
    #     self.success = self.client_socket.recv(1024).decode()
    #     # print("\nServer response (success):", self.success)
    #     self.data = self.client_socket.recv(1024).decode()
    #     # print("\nServer response (data):", self.data)

    # def close_worker_thread(self):
    #     self.task_queue.put(None)  # Sentinel value to stop the worker thread
    #     self.worker_thread.join()  # Wait for the thread to exit
    #     print("Worker thread closed")

    # def on_close(self):
    #     self.close_worker_thread()
    #     self.destroy()
    
    def start_update_function(self):
        try:
            if self.resized_up.size != 0 and self.resized_up_og.size != 0:
                self.imgLogo_1 = Image.fromarray(self.resized_up, "RGB")
                self.img_detections = Image.fromarray(self.resized_up_og, "RGB")
                w, h = self.imgLogo_1.size
                self.bg_imageLogos = customtkinter.CTkImage(self.imgLogo_1, size=(w, h))
                self.bg_image_detections = customtkinter.CTkImage(self.img_detections, size=(w, h))

                self.Thermal_Image_Label = customtkinter.CTkLabel(self.scrollable_frame_main, text=" ",
                                                                image=self.bg_image_detections, bg_color="#242424")
                self.Thermal_Image_Label.grid(row=0, column=0, padx=(20, 0), pady=(0, 0), sticky="nsew", rowspan=2)
                self.Original_Image_Label = customtkinter.CTkLabel(self.scrollable_frame_main, text="",
                                                                image=self.bg_imageLogos, bg_color="#242424")
                self.Original_Image_Label.grid(row=0, column=1, padx=(20, 0), pady=(0, 0), sticky="nsew", rowspan=2)
                self.flag_image_transmission = 0
            else:
                print("Images not generated yet!")

            self.after(1000, self.start_update_function)  # run itself again after 1000 ms

        except Exception as error:
            print("\n Update function failed because: {} \n".format(error))
            self.after(1000, self.start_update_function)
    
    def capture_keyframe(self):
        self.keyframe = self.img_detections
        w, h = self.keyframe.size
        self.keyframe_window = customtkinter.CTkToplevel()
        self.keyframe_window.title("Captured Keyframe")
        self.keyframe_window.geometry(f"{w}x{h}")
        # img_tk = ImageTk.PhotoImage(self.keyframe)
        img_ctk = customtkinter.CTkImage(self.img_detections, size=(500, 500))

        if self.keyframe_counter == 0:
            self.keyframe_label = customtkinter.CTkLabel(self.keyframe_window, image=img_ctk)
            self.keyframe_label.image = img_ctk
            self.keyframe_label.pack()
            self.keyframe_counter += 1
        else:
            self.keyframe_label.destroy()
            self.keyframe_label = customtkinter.CTkLabel(self.keyframe_window, image=img_ctk)
            self.keyframe_label.image = img_ctk
            self.keyframe_label.pack()
            self.keyframe_counter += 1

        self.keyframe_coords = np.array([self.img_coords[0], self.img_coords[1]])
        self.keyframe_vehicle_pose = np.array([self.gps_position[0], self.gps_position[1], self.gps_position[2], self.uav_attitude[2]])

        self.text_box_X.configure(state="normal")
        self.text_box_Y.configure(state="normal")
        self.text_box_X.delete(0, "end")
        self.text_box_Y.delete(0, "end")
        self.text_box_X.insert(0, "")
        self.text_box_Y.insert(0, "")
        self.text_box_X.insert(0, str(self.keyframe_coords[0]))
        self.text_box_Y.insert(0, str(self.keyframe_coords[1]))
        self.text_box_X.configure(state="readonly")
        self.text_box_Y.configure(state="readonly")

    def obtain_gps(self):
        if self.keyframe_coords[0] == 0 and self.keyframe_coords[1] == 0:
            tkmb.showwarning("Target Estimation", "No detections observed, please wait until detections appear!")
            return np.array([0, 0, 0])
        else:
            converter = Image2World(self.keyframe_coords, self.camera_res, self.FoV, self.keyframe_vehicle_pose)
            target_gps_coords = converter.main()
            self.text_box_lat.configure(state="normal")
            self.text_box_lon.configure(state="normal")
            self.text_box_lat.delete(0, "end")
            self.text_box_lon.delete(0, "end")
            self.text_box_lat.insert(0, "")
            self.text_box_lon.insert(0, "")
            self.text_box_lat.insert(0, str(target_gps_coords[0]))
            self.text_box_lon.insert(0, str(target_gps_coords[1]))
            self.text_box_lat.configure(state="readonly")
            self.text_box_lon.configure(state="readonly")
            tkmb.showinfo("Target Estimation", "GPS Coordinates of target area obtained!")
 
    def confirm_algorithm(self):
        if self.switch_all_var.get()=="on":
            if self.algorithm_choice.get() == 1:
                self.payload = {"data": "ImProc"}
                json_data = json.dumps(self.payload)
                self.client_socket.send(json_data.encode())
                self.success = self.client_socket.recv(1024).decode()
                self.response = self.client_socket.recv(1024).decode()
                # self.enqueued_sendOnBoard()
                # self.sendOnBoard()
                if self.success:
                    self.arm_system_label.configure(text="Armed", fg_color="green")
                else:
                    print("Something went wrong...!")
                # self.arm_system_label.configure(text="Armed", fg_color="green")
            elif self.algorithm_choice.get() == 2:
                self.payload = {"data": "Classifier"}
                json_data = json.dumps(self.payload)
                self.client_socket.send(json_data.encode())
                self.success = self.client_socket.recv(1024).decode()
                self.response = self.client_socket.recv(1024).decode()
                # self.enqueued_sendOnBoard()
                # self.sendOnBoard()
                if self.success:
                    self.arm_system_label.configure(text="Armed", fg_color="green")
                else:
                    print("Something went wrong...!")
            elif self.algorithm_choice.get() == 3:
                self.payload = {"data": "Yolo"}
                json_data = json.dumps(self.payload)
                self.client_socket.send(json_data.encode())
                self.success = self.client_socket.recv(1024).decode()
                self.response = self.client_socket.recv(1024).decode()
                # self.enqueued_sendOnBoard()
                # self.sendOnBoard()
                if self.success:
                    self.arm_system_label.configure(text="Armed", fg_color="green")
                else:
                    print("Something went wrong...!")
            else:
                self.arm_system_label.configure(text="Disarmed", fg_color="red")
                tkmb.showerror(title="No Algorithm Selected", message="Please select an algorithm!")
        else:
            tkmb.showerror(title="System not initialised", message="Please toggle all threads first!")

    def send_start_command(self):
        self.start_command = 1
        self.payload = {"data": "VISION," + "ON"}
        json_data = json.dumps(self.payload)
        self.client_socket.send(json_data.encode())
        self.success = self.client_socket.recv(1024).decode()
        self.response = self.client_socket.recv(1024).decode()
        # self.enqueued_sendOnBoard()
        # self.sendOnBoard()
        if self.success:
            tkmb.showinfo("Vision Module", "Vision Module is now active!")
            # print(self.data)
            self.start_update = 1
        else:
            tkmb.showerror("Vision Module", "Error sending start command!")

    def toggle_all(self):
        if self.switch_all_var.get() == "off":
            self.payload = {"data": "TERMINATION," + "OFF"}
            json_data = json.dumps(self.payload)
            self.client_socket.send(json_data.encode())
            self.success = self.client_socket.recv(1024).decode()
            self.response = self.client_socket.recv(1024).decode()
            sys.exit()
        elif self.switch_all_var.get() == "on":
            self.payload = {"data": "INITIALIZE," + "YES"}
            json_data = json.dumps(self.payload)
            self.client_socket.send(json_data.encode())
            self.success = self.client_socket.recv(1024).decode()
            self.response = self.client_socket.recv(1024).decode()
            self.img_update_func = threading.Thread(target=self.image_update)
            self.img_update_func.start()
            
    def coordinates(self):
        if self.text_box_longtitude.get() != "" and self.text_box_lat != "":
            subject = 'Fire detection module'
            body = """ Fire detection latitude and longitude : Lat = {}, Lon = {}""".format(str(self.text_box_lat.get()),str(self.text_box_longtitude.get()))
            msg_user = "Coordinates send by email to " + email_receiver[0]
            messagebox.showwarning(title="Successful Operation", message=msg_user)
            # Sending Email confirmation
            em = EmailMessage()
            em['From'] = email_sender
            em['To'] = email_receiver
            em['Subject'] = subject
            em.set_content(body)
            # Add SSL (layer of security)
            context = ssl.create_default_context()
            # Log in and send the email
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                smtp.login(email_sender, email_password)
                smtp.sendmail(email_sender, email_receiver, em.as_string())
        else:
            messagebox.showwarning("Coordinates", "Something is wrong with the coordinates!")

    def connection_command(self):
        if self.switch_connection.get() == "off":
            messagebox.showwarning("Connection","Connect to the on board server!")
            self.client_socket.close()
            self.connection_label_arm.configure(text="Disarmed", fg_color="red")
            if self.start_update == 1:
                self.start_update = 0
                self.reconnect_to_board = 1
        elif self.switch_connection.get() == "on":
            # Define the server's IP address and port
            if self.entry_ip.get() == "" and self.entry_port.get() == "":
                messagebox.showwarning("Connection Warning","Connecting to localhost:8080")
                server_ip = '127.0.0.1'  # Change this to the server's IP
                server_port = 8080  # Change this to the server's port

                # Create a socket to connect to the server
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            elif self.entry_ip.get() == "" and self.entry_port.get() != "":
                messagebox.showwarning("Connection Warning", "Connecting to localhost:{}".format(self.entry_port.get()))
                server_ip = '127.0.0.1'  # Change this to the server's IP
                server_port = int(self.entry_port.get())  # Change this to the server's port

                # Create a socket to connect to the server
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            elif self.entry_ip.get() != "" and self.entry_port.get() == "":
                messagebox.showwarning("Connection Warning", "Connecting to {}:8080".format(self.entry_ip.get()))
                server_ip = self.entry_ip.get()  # Change this to the server's IP
                server_port = 8080  # Change this to the server's port

                # Create a socket to connect to the server
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            else:
                messagebox.showwarning("Connection Warning", "Connecting to {}:{}".format(self.entry_ip.get(),self.entry_port.get()))
                server_ip = self.entry_ip.get()  # Change this to the server's IP
                server_port = int(self.entry_port.get())  # Change this to the server's port

                # Create a socket to connect to the server
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Connect to the server
            server_address = (server_ip, server_port)
            self.client_socket.connect(server_address)
            self.connection_label_arm.configure(text="Armed", fg_color="green")
            if self.reconnect_to_board:
                self.start_update = 1

    def decode_numpy(obj):
        if "__ndarray__" in obj:
            # Reconstruct NumPy array from metadata
            return np.frombuffer(obj["data"], dtype=obj["dtype"]).reshape(obj["shape"])
        return obj

    def image_update(self):  
        self.image_request()
        self.after(1000, self.image_update)
            
    def image_request(self):
        try:
            # Initial handshake
            self.payload = {"data": "IMG"}
            json_data = json.dumps(self.payload)
            self.client_socket.send(json_data.encode())
            
            # Set timeout for receiving data
            self.client_socket.settimeout(10.0)  # 10 second timeout
            
            # Receive initial responses
            try:
                self.success = self.client_socket.recv(1024).decode()
                self.response = self.client_socket.recv(1024).decode()
                self.img_avail = self.client_socket.recv(1024).decode()
                
                if not all([self.success, self.response, self.img_avail]):
                    raise ConnectionError("Failed to receive complete handshake response")
                    
                print(f"Image Request Handshake: {self.success}")
                print(f"Server Response: {self.response}")
                print(f"Server Response (Image Status): {self.img_avail}")
                
                if self.img_avail != "ImgAvail":
                    print("Images not available yet!")
                    return
                    
            except socket.timeout:
                print("Timeout while receiving handshake responses")
                return
                
            # Receive stream lengths
            try:
                packed_data = b""
                remaining = 6 * payload_size
                
                while remaining > 0:
                    chunk = self.client_socket.recv(min(remaining, 4096))
                    if not chunk:
                        raise ConnectionError("Connection closed while receiving stream lengths")
                    packed_data += chunk
                    remaining -= len(chunk)
                
                # Extract stream lengths
                stream_lengths = struct.unpack("QQQQQQ", packed_data)
                msg_size = stream_lengths[0]
                frame_buf_size = stream_lengths[1]
                og_frame_buf_size = stream_lengths[2]
                coords_buf_size = stream_lengths[3]
                gps_buf_size = stream_lengths[4]
                attitude_buf_size = stream_lengths[5]
                
                total_expected_size = sum([frame_buf_size, og_frame_buf_size, coords_buf_size, 
                                        gps_buf_size, attitude_buf_size])
                
                if total_expected_size != msg_size:
                    raise ValueError(f"Size mismatch: expected {msg_size}, sum of parts is {total_expected_size}")
                    
            except socket.timeout:
                print("Timeout while receiving stream lengths")
                return
                
            # Receive image and data streams
            try:
                packed_data = b""
                remaining = msg_size
                
                while remaining > 0:
                    chunk = self.client_socket.recv(min(remaining, 128*1024))
                    if not chunk:
                        raise ConnectionError("Connection closed while receiving data streams")
                    packed_data += chunk
                    remaining -= len(chunk)
                    
                # Verify received data size
                if len(packed_data) != msg_size:
                    raise ValueError(f"Received data size {len(packed_data)} doesn't match expected {msg_size}")
                    
                # Extract individual streams
                current_pos = 0
                frame_stream = packed_data[current_pos:current_pos + frame_buf_size]
                current_pos += frame_buf_size
                
                og_frame_stream = packed_data[current_pos:current_pos + og_frame_buf_size]
                current_pos += og_frame_buf_size
                
                coords_stream = packed_data[current_pos:current_pos + coords_buf_size]
                current_pos += coords_buf_size
                
                gps_pos_stream = packed_data[current_pos:current_pos + gps_buf_size]
                current_pos += gps_buf_size
                
                attitude_stream = packed_data[current_pos:current_pos + attitude_buf_size]
                
                # Deserialize data
                try:
                    frame = pickle.loads(frame_stream)
                    og_frame = pickle.loads(og_frame_stream)
                    img_coords = pickle.loads(coords_stream)
                    gps_pos = pickle.loads(gps_pos_stream)
                    uav_attitude = pickle.loads(attitude_stream)

                except pickle.UnpicklingError as e:
                    raise ValueError(f"Failed to deserialize received data: {str(e)}")
                    
                # Process images
                try:
                    # Save images
                    cuu_time = datetime.now().strftime("%Y%m%d-%H%M%S")
                    filename = f'img{cuu_time}.png'
                    full_path_detection = os.path.join(folder_images_detection, filename)
                    full_path_og = os.path.join(folder_images_original, filename)
                    
                    cv2.imwrite(full_path_detection, frame)
                    cv2.imwrite(full_path_og, og_frame)
                    
                    # Process for display
                    img_det = cv2.imread(full_path_detection)
                    img_og = cv2.imread(full_path_og)

                    if img_det is None or img_og is None:
                        raise ValueError("Failed to read saved images")
                        
                    img_det = cv2.cvtColor(img_det, cv2.COLOR_BGR2RGB)
                    img_og = cv2.cvtColor(img_og, cv2.COLOR_BGR2RGB)
                    
                    # cv2.imshow("Detections", img_det)
                    # cv2.imshow("Original", img_og)

                    up_points = (500, 500)
                    self.resized_up = cv2.resize(img_det, up_points, interpolation=cv2.INTER_LINEAR)
                    self.resized_up_og = cv2.resize(img_og, up_points, interpolation=cv2.INTER_LINEAR)
                    
                    # Store metadata
                    self.img_coords = img_coords
                    self.gps_position = gps_pos
                    self.uav_attitude = uav_attitude
                    print(self.img_coords)
                    print(self.gps_position)
                    print(self.uav_attitude)
                    
                    print("Images processed successfully!")
                    
                except Exception as e:
                    raise ValueError(f"Failed to process images: {str(e)}")
                    
            except socket.timeout:
                print("Timeout while receiving data streams")
                return
                
        except Exception as error:
            print(f"Error in image_request: {str(error)}")
            # Optionally, update UI to show error
            if hasattr(self, 'connection_label_arm'):
                self.connection_label_arm.configure(text="Error", fg_color="red")
        finally:
            # Reset socket timeout to default
            self.client_socket.settimeout(None)

if __name__ == "__main__":
    login_screen = LoginUIFirst()
    login_screen.mainloop()