import time
from commandFilter import commandFilter
from gripperSerialControl import Gripper

import sys
import logging

import rtde.rtde as rtde
import rtde.rtde_config as rtde_config

import argparse

_last = None

def monotonic_ms():
    global _last
    t = time.time()
    if _last is not None and t < _last:
        t = _last
    _last = t
    return t

# parse args
parser = argparse.ArgumentParser()
parser.add_argument('--gripper_id', type=int, default=9, help='Gripper device ID (default: 9)')
parser.add_argument('--gripper_port', default='/dev/ttyTool', help='TCP port or serial port of the gripper. 54321 for RS485 URCAP. 63352 for Robotiq URCAP. COM0 (Windows) or /dev/tty/USB0 (Linux) for serial.')
parser.add_argument('--rtde_input_int_register', type=int, default=24, help='Id of the rtde input int register where is saved the gripper position request.')
parser.add_argument('--minSpeedPosDelta',type=int,default=10,help='If the distance between current position and position request is less than this value the gripper will move at its minimum speed. ')
parser.add_argument('--maxSpeedPosDelta',type=int,default=100,help='If the distance between current position and position request is more than this value the gripper will move at its maximum speed. ')
parser.add_argument('--disableContinuousGrip',action='store_true',dest='disableContinuousGrip',help='By default the gripper continuously try to close on the object even after object detection. If disable the gripper stop at the position where the object has been detected.')
parser.add_argument('--disableAutoLock', action='store_true',dest='disableAutoLock',help='By default when the gripper detect an object it try to secure it with full force and speed. If disable the gripper will grip at low speed and force resulting is a weaker grip.')
parser.add_argument('--minimalMotion',type=int,default=1,help='The gripper goes to the requested position only if the requested position is at a distance larger than minimalMotion')

args = parser.parse_args()


# Python 2 script

register_number = args.rtde_input_int_register  # <-- your variable

filename = "record_configuration.xml"

with open(filename, "r") as f:
    content = f.read()

# Replace 24 with variable value
content = content.replace(
    "input_int_register_24",
    "input_int_register_%d" % register_number
)

with open(filename, "w") as f:
    f.write(content)

print("Replacement done.")

#RTDE configuration
CONFIG_FILE="record_configuration.xml"
HOST = "localhost"
PORT = 30004

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

#Gripper configuration
gripper=Gripper(args.gripper_port,args.gripper_id)
gripper.connect()
gripper.activate_gripper()


def updateList(data,value):
    data[1:]=data[:-1]
    data[0]=value

###################
#Main program loop
###################
def run_robotiqRTDE():
    try:
        
        
        #Loop variables
        GRIP_NOT_REQUESTED = 0
        GRIP_REQUESTED = 1
        GRIP_VALIDATED = 2

        NO_COMMAND =0
        WRITE_READ_COMMAND = 1
        READ_COMMAND = 2

        #[t-1,t-2]
        #The gripper can recieve command at a maximum of 60Hz. Last 30 commmand give an history of minimum0.5s
        #The more recent command is at the beginning of the list
        commandHistory={}
        commandHistory["time"]=[monotonic_ms()]*30
        time.sleep(1)
        updateList(commandHistory["time"],monotonic_ms())
        
        commandHistory["positionCommand"]=[0]*30
        commandHistory["position"]=[0]*30
        commandHistory["positionRequest"]=[0]*30
        commandHistory["speedCommand"]=[0]*30
        commandHistory["forceCommand"]=[0]*30
        commandHistory["detection"]=[0]*30
        commandHistory["gripCommand"]=[GRIP_NOT_REQUESTED]*30
        elapsedTime = 0
        commandStatus=None
        statusUpdate=None

        while True:
            #Get the requested position saved in RTDE
            state = con.receive()
            reg = args.rtde_input_int_register
            t0_RequestPosition = getattr(state, "input_int_register_%d" % reg)

            if t0_RequestPosition > 255:
                t0_RequestPosition=255
                print "Position request is not in the range 0-255: %.0f" % (t0_RequestPosition)
            if t0_RequestPosition < 0:
                t0_RequestPosition=0
                print "Position request is not in the range 0-255: %.0f" % (t0_RequestPosition)
            
            #2- Get time
            now=monotonic_ms()
            elapsedTime = now - commandHistory["time"][0]
            if elapsedTime<0:
                raise Exception("Negative elapsed time {} previous time {} , current time {}".format(elapsedTime,commandHistory["time"][0],now)
)
           
            
            #2 Build gripper command
            command=commandFilter(t0_RequestTime=now,
                                  t0_RequestPosition=t0_RequestPosition,
                                  commandHistory=commandHistory,
                                  statusUpdate=statusUpdate,
                                  minSpeedPosDelta=args.minSpeedPosDelta,
                                  maxSpeedPosDelta=args.maxSpeedPosDelta,
                                  continuousGrip=not args.disableContinuousGrip,
                                  autoLock=not args.disableAutoLock,
                                  minimalMotion=args.minimalMotion)
            if command["execution"]==WRITE_READ_COMMAND:
                commandStatus=gripper.writePSFreadStatus(command["position"],command["speed"],command["force"])
                if command["wait"]>0:
                    time.sleep(command["wait"])
                updateList(commandHistory["time"],now)
                updateList(commandHistory["positionCommand"],command["position"])
                updateList(commandHistory["position"],commandStatus["gPO"])
                updateList(commandHistory["positionRequest"],t0_RequestPosition)
                updateList(commandHistory["speedCommand"],command["speed"])
                updateList(commandHistory["forceCommand"],command["force"])
                updateList(commandHistory["detection"],commandStatus["gOBJ"])
                updateList(commandHistory["gripCommand"],command["grip"])

            elif command["execution"]==READ_COMMAND:
                statusUpdate=gripper.readStatus()
                statusUpdate["time"]=now
            else:             
                pass
            
            time.sleep(0.01)

    except KeyboardInterrupt:
        print "Stopping robotiq RTDE"

    finally:
        gripper.close()
        con.disconnect()

if __name__ == '__main__':
    run_robotiqRTDE()
