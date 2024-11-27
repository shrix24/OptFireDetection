# Import libraries
import numpy as np
#import glob
import time
import requests
from signalrcore.hub_connection_builder import HubConnectionBuilder
import base64
from datetime import datetime
import pickle
import struct
# print(sys.path)
# from DecisionClass import Decision_Distance
# from Runway_Detection_Classesv1 import *
# from SURF_extraction import CUDA_SURF_extraction_matching
# from Detection import Detection
# from Tracking import Tracking_Algorithm
from GlobalVars import global_vars



def getMissionLand(CONNECTION_URL, token):
    # Create authorised header
    headers = {"Authorization": token}

    # Get the available platform Ids
    print("Getting Available Ids...")
    response = requests.get(CONNECTION_URL + '/app/Account/getPlatforms', headers=headers)
    firstPlatformInfo = response.json()[0]
    autopilotId = firstPlatformInfo["id"]
    print("Found a platform with Id: %s" % autopilotId)

    # Get the available mission
    print("Getting Mission...")
    response = requests.post(CONNECTION_URL + '/autopilot/Mission/getMission?platformId=' + autopilotId, headers=headers)
    # response = requests.post(requestURL, headers=headers)
    firstPlatformInfo = response.json()
    # print(firstPlatformInfo['data'])

    startAlg_cv_ind = len(firstPlatformInfo['data']) - 1 # which waypoint the computer vision algorithm will be initiated
    print(startAlg_cv_ind)
    # latMission = firstPlatformInfo['waypoints'][startAlg_cv_ind]['location']['latDeg']# location of the last waypoint (landing)
    # lngMission = firstPlatformInfo['waypoints'][startAlg_cv_ind]['location']['lngDeg']
    # print(firstPlatformInfo['waypoints'][startAlg_cv_ind]['location'])
    # print(latMission, lngMission)
    return startAlg_cv_ind  #,latMission,lngMission

#### Configure DA API ####
# Cloud Control -> "https://www.distributed-avionics.com"
# CONNECTION_URL = "https://cloud.distributed-avionics.com"

# USERNAME = "k.tsapparellas@sheffield.ac.uk"
# PASSWORD = "cloudSwarmVideo"

# CONNECTION_URL = "http://192.168.134.155:8000"
CONNECTION_URL = global_vars.IP_PLATFORM

USERNAME = "Admin"
PASSWORD = "Distributed"

# get an authorised token
print("Getting Token...")
payload = {"username": USERNAME, "password": PASSWORD } #replace these with your own for CC, GC or PC as required
response = requests.post(CONNECTION_URL + '/Authentication/authenticate', json = payload)
token = "Bearer " + response.json()["token"] # important to add 'Bearer' to the start of the token here
# print("Got Token: " + token)
# # Create authorised header
headers = {"Authorization": token}
msg_data = []
# msg_data = base64.b64encode(msg_data)
global_vars.start_cv_waypoint = getMissionLand(CONNECTION_URL,token)
# global_vars.start_cv_waypoint = 6
# global_vars.landing_start_flag =1
#setup logging
import logging
handler = logging.StreamHandler()
logging.disable() # disable it by default... it's verbose!

def abort_landing(CONNECTION_URL, token):
    # Create authorised header
    headers = {"Authorization": token}

    # Get the available platform Ids
    print("Getting Available Ids...")
    response = requests.get(CONNECTION_URL + '/app/Account/getPlatforms', headers=headers)
    firstPlatformInfo = response.json()[0]
    autopilotId = firstPlatformInfo["id"]
    print("Found a platform with Id: %s" % autopilotId)

    # Get the available mission
    print("Aborting Mission...")
    response = requests.post(CONNECTION_URL + '/autopilot/Command/abortLanding?platformId=' + autopilotId, headers=headers)
    # response = requests.post(requestURL, headers=headers)

# declare the message handlers
def handleHeartbeat(data):
    print("Heartbeat | Id: %s, time: %s, isConnected: %s, failsafe: %s, isControllable: %s, autopilotType: %s, name: %s, failsafeReasons: %s" \
        % (data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7]))

def handleMode(data):
    print("Mode | Id: %s, mode: %s, armed: %s, grounded: %s, time: %s" % (data[0], data[1], data[2], data[3], data[4]))

def handleLocation(data):
    # print(data)
    global gps_uav_alt
    gps_uav_lng = data[0]['data']['lngDeg']
    gps_uav_lat = data[0]['data']['latDeg']
    global_vars.gps_uav_alt = data[0]['data']['altM']
    
def handleAttitude(data):
    roll = data[0]['data']['rollDeg']
    pitch = data[0]['data']['pitchDeg']
    yaw = data[0]['data']['yawDeg']
    # print(yaw)
    #print("Aircraft Attitude | Id: %s, attitude: %s, time: %s" % (data[0], data[1], data[2]))
    # Attitude is in degrees

def handleAcceleration(data):
    print("Aircraft Acceleration | Id: %s, acceleration: %s, time: %s" % (data[0], data[1], data[2]))

def handleSpeed(data):
    print("Aircraft Speed | Id: %s, aircraftSpeeds: %s, time: %s" % (data[0], data[1], data[2]))
    # Airspeed is the Equivalent Airspeed (this is calibrated on a per plane basis)

def handleThrottle(data):
    print("Throttle Percentage | Id: %s, throttle: %d" % (data[0], data[1]))

def handleCommsQuality(data):
    print("Comms Quality | Id: %s, quality: %d" % (data[0], data[1]))
    # Quality can vary from 0 to 1 and indicates what percentage of sent packets have been received

def handleWindStatus(data):
    print(data)
    print("Wind Status | Id: %s, speedMps: %s, directionDeg: %s, verticalSpeedMps: %s" % (data[0], data[1], data[2], data[3]))

def handleCurrentWaypoint(data):
    #print(data)
    # print("Current Waypoint | Id: %s, index: %d" % (data[0], data[1]))
    global curr_Waipoint, landing_start_flag
    #print(data)
    curr_Waipoint = data[0]['data']['index']
    # print(curr_Waipoint)
    # print(global_vars.start_cv_waypoint)
    # print(global_vars.gps_uav_alt)
    if (curr_Waipoint == global_vars.start_cv_waypoint):
        if global_vars.abort_var == 0:
           global_vars.landing_start_flag = 1
        else:
            global_vars.landing_start_flag = 0
    else:
        global_vars.landing_start_flag = 0
        global_vars.abort_var = 0

def handleGoalPosition(data):
    print("Goal Position | Id: %s, location: %s" % (data[0], data[1]))
    # location is in decimal degrees and altitude is in meters AMSL relative to EGM96 Geiod

def handleStatusText(data):
    print("Status Text | Id: %s, time: %s, text: %s, severity: %d" % (data[0], data[1, data[2], data[3]]))

def handleAccelerometerCalibrationPosition(data):
    print("Accelerometer Calibration Position | Id: %s, position: %s, success %s" % (data[0], data[1], data[2]))

def handleMagnetometerCalibrationProgress(data):
    print("Magnotometer Calibration Progress | Id: %s, mag Id: %s, progress %s" % (data[0], data[1], data[2]))

def handleRCInput(data):
    print("RC Input | Id: %s, rc Input: %d" % (data[0], data[1]))

def handleServoOutput(data):
    print("Servo Output | Id: %s, servo output: %d" % (data[0], data[1]))

def handleADSBCollision(data):
    print("ADSB Collision | Detector Id: %s, Collision: %s" % (data[0], data[1]))

def handleAirspeedRawInfo(data):
    print(data)
    print("Airspeed Raw Info | Id: %s, RawInfoList: %s, time: %s" % (data[0], data[1], data[2]))

def handleGroundDistanceRawInfo(data):
    print("Ground Distance Raw Info | Id: %s, RawInfoList: %s, time: %s" % (data[0], data[1], data[2]))

def handleGPSRawInfo(data):
    print("GPS Raw Info | Id: %s, RawInfoList: %s, time: %s" % (data[0], data[1], data[2]))


# Ground Hub only
def handleRadioStatus(data):
    print("Radio Status | Id: %s, radio status: %s" % (data[0], data[1]))

# declare connection event handlers
def onOpen():
    print("Connection opened")

def onClose():
    print("Connection closed")

def onError(data):
    print("Error | %s" % data.error)


# create connection
print("### Starting SignalR Autopilot Hub demo ###")

# created the connection object
# add the JWT to start the connection
# this will only produce anything if you turn on logging at the start
hub_connection = HubConnectionBuilder()\
    .with_url(CONNECTION_URL + "/autopilotHub", options={
        "headers": {
            "Authorization" : token}
        })\
    .with_automatic_reconnect({
        "type": "raw",
        "keep_alive_interval": 2
    })\
    .configure_logging(logging.DEBUG, socket_trace=True, handler=handler)\
    .build()

#sign up to start stop and error events
hub_connection.on_open(onOpen)
hub_connection.on_close(onClose)
hub_connection.on_error(onError)

hub_connection.on("BroadcastLocation", handleLocation)
hub_connection.on("BroadcastCurrentWaypoint", handleCurrentWaypoint)

# hub_connection.start()

# main = CUDA_SURF_extraction_matching() # initialising classes for runway detection
# main.select_ref_dir_board()
# main.surf_init_reference_imgs()
# detection_algorithm = Detection(main) # detection class contains all functions for feature matching
