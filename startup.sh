#!/bin/bash

# Set the path to your Python script (replace with actual path)
PYTHON_SCRIPT_PATH=/home/da/X-Plane-ULTRA-Simulation/Scripts/Source_Code/mainThread.py

# Control the fan speed
# sudo jetson_clocks --fan
python3 --version
# Activate virtual environment
source /home/da/VBNS/projectSWARM/bin/activate
python3 --version
cd ~
cd /home/da/X-Plane-ULTRA-Simulation/Scripts/Source_Code
# Run the Python script with arguments (if required)
/home/da/VBNS/projectSWARM/bin/python3.9 $PYTHON_SCRIPT_PATH

# Exit the script
exit 0
