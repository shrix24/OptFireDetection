import customtkinter
from tkinter import *
from tkinter import messagebox
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
from coord_converter_v2 import Image2World

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
folder_images_detection = folder_images + "\detection"
folder_images_original = folder_images + "\original"
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
            # self.app.start_update_function()
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

        # Coordinate Output Section
        self.appearance_mode_label = customtkinter.CTkLabel(self.tabview_sysout.tab(self.tab_output),
                                                            text="Image Coordinates")
        self.appearance_mode_label.grid(row=0, column=2, padx=(10, 10), pady=(5, 5), sticky="nsew")
        self.text_box_X = customtkinter.CTkEntry(self.tabview_sysout.tab(self.tab_output), placeholder_text="X Coordinates", state='disabled')
        self.text_box_X.grid(row=1,column=2, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.text_box_Y = customtkinter.CTkEntry(self.tabview_sysout.tab(self.tab_output), placeholder_text="Y Coordinates", state='disabled')
        self.text_box_Y.grid(row=2, column=2, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.text_label_X = customtkinter.CTkLabel(self.tabview_sysout.tab(self.tab_output), text="X:")
        self.text_label_X.grid(row=1, column=1, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.text_label_Y = customtkinter.CTkLabel(self.tabview_sysout.tab(self.tab_output), text="Y:")
        self.text_label_Y.grid(row=2, column=1, padx=(10, 10), pady=(10, 10), sticky="nsew")

        # GPS Coordinate Output Section
        self.label_gps_coords = customtkinter.CTkLabel(self.tabview_sysout.tab(self.tab_output), text="GPS Coordinates")
        self.label_gps_coords.grid(row=0, column=4, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.text_box_lat = customtkinter.CTkEntry(self.tabview_sysout.tab(self.tab_output), placeholder_text="Latitude", state="disabled")
        self.text_box_lat.grid(row=1, column=4, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.text_box_lon = customtkinter.CTkEntry(self.tabview_sysout.tab(self.tab_output), placeholder_text="Longitude", state="disabled")
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

    def start_update_function(self):
        if self.start_update==1:
            # global counter_images
            try:
                self.image_request_update()
                self.after(500, self.start_update_function)  # run itself again after 1000 ms
            except:
                self.after(500, self.start_update_function)
    
    def capture_keyframe(self):
        self.keyframe = self.img_detections
        w, h = self.keyframe.size
        self.keyframe_window = customtkinter.CTkToplevel()
        self.keyframe_window.title("Captured Keyframe")
        self.keyframe_window.geometry(f"{w}x{h}")
        img_tk = ImageTk.PhotoImage(self.keyframe)

        keyframe_label = customtkinter.CTkLabel(self.keyframe_window, image=img_tk)
        keyframe_label.image = img_tk
        keyframe_label.pack()

    def obtain_gps(self, img_coordinates, camera_res, FoV, vehicle_pose):
        converter = Image2World(img_coordinates, camera_res, FoV, vehicle_pose)
        target_gps_coords = converter.main()

        return target_gps_coords
 
    def confirm_algorithm(self):
        if self.switch_all_var.get()=="on":
            if self.algorithm_choice.get() == 1:
                self.payload = {"data": "ImProc"}
                self.sendOnBoard()
                if self.success:
                    self.arm_system_label.configure(text="Armed", fg_color="green")
                else:
                    print("Something went wrong...!")
                # self.arm_system_label.configure(text="Armed", fg_color="green")
            elif self.algorithm_choice.get() == 2:
                self.payload = {"data": "Classifier"}
                self.sendOnBoard()
                if self.success:
                    self.arm_system_label.configure(text="Armed", fg_color="green")
                else:
                    print("Something went wrong...!")
            elif self.algorithm_choice.get() == 3:
                self.payload = {"data": "Yolo"}
                self.sendOnBoard()
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
        self.sendOnBoard()
        if self.success:
            tkmb.showinfo("Vision Module", "Vision Module is now active!")
        else:
            print("Something went wrong!")
            self.reconnect_to_board = 1

    def toggle_all(self):
        if self.switch_all_var.get() == "off":
            self.payload = {"data": "TERMINATION," + "OFF"}
            self.sendOnBoard()
            print(self.data)
            sys.exit()
        elif self.switch_all_var.get() == "on":
            self.payload = {"data": "START," + "YES"}
            self.sendOnBoard()
            print(self.data)
            self.start_update = 1

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
    
    def sendOnBoard(self):
        # response = requests.post(CONNECTION_URL + '/app/CustomData/sendViaInternet', json=self.payload, headers=headers) # sendViaInternet
        # response = requests.post(CONNECTION_URL + '/app/CustomData/sendToHub', json=self.payload, headers=headers)
        # self.success = response.ok
        # Convert the dictionary to a JSON string
        json_data = json.dumps(self.payload)
        # Send the message to the server
        self.client_socket.send(json_data.encode())
        self.success = self.client_socket.recv(1024).decode()
        self.data = self.client_socket.recv(1024).decode()
        # print(f"Server response: {response}")

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

    def image_request_update(self):
        # used in handling binary data from network connections
        data_img = b""
        self.receive_img = 1
        # messagebox.showwarning(title="Image Transmission",
        #                        message="Image transmission can lead to slower operation of the system")
        # payload = {"targetPlatformIds": [autopilotId],"data": msg}
        self.flag_image_transmission = 1
        self.payload = {"data": "IMG," + "S"}
        self.sendOnBoard()
        print("Image Request Handshake: ", self.success)

        if self.data == "ImageSend":
            while len(data_img) < payload_size:
                packet = self.client_socket.recv(8 * 1024)
                if not packet: break
                data_img += packet
            packed_msg_size = data_img[:payload_size]
            data_img = data_img[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]
            frame_size = struct.unpack("Q", packed_msg_size)[1]
            og_frame_size = struct.unpack("Q", packed_msg_size)[2]

            while len(data_img) < msg_size:
                data_img += self.client_socket.recv(8 * 1024)
            
            composite_frame_data = data_img[:msg_size]
            data_img = data_img[msg_size:]
            frame_data = composite_frame_data[:frame_size]
            og_frame_data = composite_frame_data[frame_size:frame_size+og_frame_size]
            
            frame = pickle.loads(frame_data)
            og_frame = pickle.loads(og_frame_data)
            cuu_time = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = 'img' + cuu_time + '.png'
            full_path_detection = os.path.join(folder_images_detection, filename)
            full_path_og = os.path.join(folder_images_original, filename)
            cv2.imwrite(full_path_detection, frame)
            cv2.imwrite(full_path_og, og_frame)

            img_det = cv2.imread(full_path_detection)
            img_og = cv2.imread(full_path_og)
            img_det = cv2.cvtColor(img_det, cv2.COLOR_BGR2RGB)
            img_og = cv2.cvtColor(img_og, cv2.COLOR_BGR2RGB)
            up_width = 800
            up_height = 640
            up_points = (up_width, up_height)
            resized_up = cv2.resize(img_det, up_points, interpolation=cv2.INTER_LINEAR)
            resized_up_og = cv2.resize(img_og, up_points, interpolation=cv2.INTER_LINEAR)

            self.imgLogo_1 = Image.fromarray(resized_up)
            self.img_detections = Image.fromarray(resized_up_og)
            w, h = self.imgLogo_1.size
            self.bg_imageLogos = customtkinter.CTkImage(self.imgLogo_1, size=(w, h))
            self.bg_image_detections = customtkinter.CTkImage(self.img_detections, size=(w, h))

            self.Thermal_Image_Label = customtkinter.CTkLabel(self.scrollable_frame_main, text=" ",
                                                              image=self.bg_image_detections, bg_color="#242424")
            self.bg_imageLogos_label.grid(row=0, column=0, padx=(20, 0), pady=(0, 0), sticky="nsew", rowspan=2)
            self.Original_Image_Label = customtkinter.CTkLabel(self.scrollable_frame_main, text="",
                                                               image=self.bg_imageLogos, bg_color="#242424")
            self.Original_Image_Label.grid(row=0, column=1, padx=(20, 0), pady=(0, 0), sticky="nsew", rowspan=2)
            self.flag_image_transmission = 0

        # self.after(10, self.image_request_update())  # run itself again after 1000 ms

if __name__ == "__main__":
    login_screen = LoginUIFirst()
    login_screen.mainloop()