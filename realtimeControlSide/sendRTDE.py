import sys
import pygame

#sys.path.append("..")
#sys.path.insert(0, os.getcwd())
import logging

import rtde.rtde as rtde
import rtde.rtde_config as rtde_config

def map_0_255(x):
    """
    Map a value from [-1, 1] to [0, 255].
    """
    return int((x + 1) * (255-0)/(1-(-1))+0)

CONFIG_FILE="record_configuration.xml"
HOST = "localhost"
PORT = 30004
FREQUENCY = 100

logging.basicConfig(level=logging.INFO)

conf = rtde_config.ConfigFile(CONFIG_FILE)
input_names, input_types = conf.get_recipe("in")
output_names, output_types = conf.get_recipe("out")

print(input_names, input_types)

con = rtde.RTDE(HOST, PORT)
con.connect()

# get controller version
con.get_controller_version()

setp = con.send_input_setup(input_names, input_types)
con.send_output_setup(output_names, output_types)

setp.input_int_register_24=0

# start data synchronization
if not con.send_start():
    sys.exit()

keep_running = True

pygame.init()
pygame.joystick.init()
js = pygame.joystick.Joystick(0)
js.init()
print("Joystick:", js.get_name())

while keep_running:
    try:
        con.receive()
        pygame.event.pump()
        joy0 = js.get_axis(3)  # Right stick Y
        pos = map_0_255(joy0)
        setp.input_int_register_24=pos
        con.send(setp)

    except KeyboardInterrupt:
        keep_running = False
    except rtde.RTDEException:
        con.disconnect()
        sys.exit()
