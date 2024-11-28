#!/bin/bash

# Activate Virtual Environment
source /home/da/VBNS/projectSWARM/bin/activate#

# Run installation command to install all required packages
pip install -r requirements.txt

# Run the Python script with arguments (if required)
/home/da/VBNS/projectSWARM/bin/python3.9 $PYTHON_SCRIPT_PATH

# Exit the script
exit 0