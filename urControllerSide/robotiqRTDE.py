import minimalmodbus
import serial
import time
from commandFilter import commandFilter

import sys
import os

#sys.path.append("..")
#sys.path.insert(0, os.getcwd())
import logging

import rtde.rtde as rtde
import rtde.rtde_config as rtde_config


#gripper functions
def reset(gripper):
    gripper.write_registers(1000,[0,0,0])
def activate(gripper):
    gripper.write_registers(1000,[0b0000100100000000,0,0])
def writePSF(gripper,position,speed=0,force=0):
    """Go to the position with determined speed and force.
    
    Args:
        - position (int): Position of the gripper. Integer between 0 and 255.\
        0 being the open position and 255 being the close position.
        - speed (int): Gripper speed between 0 and 255
        - force (int): Gripper force between 0 and 255
    
    Returns:
        - objectDetected (bool): True if object detected
        - position (int): End position of the gripper in bits
    """
    position=int(position)
    speed=int(speed)
    force=int(force)

    #Check input value
    if position>255:
        raise Exception("Position value cannot exceed 255")
    elif position<0:
        raise Exception("Position value cannot be under 0")
    if speed>255:
        raise Exception("Speed value cannot exceed 255")
    elif speed<0:
        raise Exception("Speed value cannot be under 0")
    if force>255:
        raise Exception("Force value cannot exceed 255")
    elif force<0:
        raise Exception("Force value cannot be under 0")
    gripper.write_registers(1001,[position,speed * 0b100000000 + force])
def writeP(gripper,position):
    position=int(position)

    #Check input value
    if position>255:
        raise Exception("Position value cannot exceed 255")
    elif position<0:
        raise Exception("Position value cannot be under 0")
    gripper.write_registers(1001,[position])
def estimateAndWaitComplete(gripper,currentPos,requestedPos,speed):
    GRIPPER_VMAX = 332  # max speed in steps per second
    GRIPPER_VMIN = 68   # min speed in steps per second
    posBitPerSecond = GRIPPER_VMIN + ((GRIPPER_VMAX-GRIPPER_VMIN)/255)*speed
    timeToRequestedPos = abs(requestedPos-currentPos)/posBitPerSecond
    time.sleep(timeToRequestedPos)
#Creation of gripper object and activation

gripper = minimalmodbus.Instrument('/dev/ttyTool',9)

gripper.serial.baudrate = 115200
gripper.serial.bytesize = 8
gripper.serial.parity = serial.PARITY_NONE
gripper.serial.stopbits = 1
gripper.serial.timeout=0.2
#gripper.debug = True

#Gripper activation

reset(gripper)
activate(gripper)
time.sleep(2)

CONFIG_FILE="record_configuration.xml"
HOST = "localhost"
PORT = 30004
FREQUENCY = 500

logging.basicConfig(level=logging.INFO)

conf = rtde_config.ConfigFile(CONFIG_FILE)
output_names, output_types = conf.get_recipe("out")

con = rtde.RTDE(HOST, PORT)
con.connect()

# get controller version
con.get_controller_version()

con.send_output_setup(output_names, output_types)

# start data synchronization
if not con.send_start():
    logging.error("Unable to start synchronization")
    sys.exit()



previousRequestTime = time.time()
previousPosRequest = 0
previousPos = 0
previousSpeed = 0
previousForce = 0


keep_running = True
while keep_running:
    try:
        state = con.receive()
        pos= state.input_int_register_24
        
        now = time.time()
        elapsedTime = now - previousRequestTime
        
        #"""
        command = commandFilter(pos,now,previousRequestTime,previousPos,previousPosRequest,previousSpeed,previousForce,5,110)#5,110
        
        previousRequestTime = now
        previousPosRequest = command["positionRequest"]
        previousPos = command["currentPosition"]
        previousSpeed = command["speedRequest"]
        previousForce = command["forceRequest"]
        if command["toExecute"]:
            print "%.4f maPrevious P_request %.0f, P%.0f , S %.0f, F%.0f, New P_request %.0f, P%.0f, S %.0f, F%.0f" % (
                elapsedTime,
                previousPosRequest,
                previousPos,
                previousSpeed,
                previousForce,
                command['positionRequest'],
                command['currentPosition'],
                command['speedRequest'],
                command['forceRequest']
            )
            writePSF(gripper,command["positionRequest"],command["speedRequest"],command["forceRequest"])
            if command["waitTime"]>0:
                time.sleep(command["waitTime"])
        
        #"""
        #print pos
        time.sleep(0.001)

    except KeyboardInterrupt:
        keep_running = False
    except rtde.RTDEException:
        con.disconnect()
        sys.exit()

