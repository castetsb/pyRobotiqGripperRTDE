====================
pyRobotiqGripperRTDE
====================

Introduction
============

This package provide software tools to control in a contious manner (realtime) a Robotiq gripper connected at the wrist of a UR robot from outside through RTDE.
The code have been tested on URSim with a 2F85 gripper.

The package is composed of 2 folders:

- urController: Software to deploy on UR controller which contains:
    - python2 dependencies packaged in tar.gz files
    - install.sh file to install dependencies
    - python2 script to monitor RTDE register and send appropriate commands to the gripper connected a thte wrist of the robot.
- realtimeController: Software to deploy on the PC from which the realtime gripper control is done. It contains:
    - urrtde package in tar.gz format
    - Example of python code which detect the position of a joystick and write the corresponding gripper position in RTDE register.

Installation
============
Installation on UR controller
-----------------------------
On UR the UR robot, setup the tool communication to be serial as below (I am not sure about the RX and TX settings).

.. image:: attachments/toolSerialSettings.JPG

Connect to the UR robot using a FTP client like Filezilla (https://filezilla-project.org/).
Default parameters to connect to robot FTP are the following:

- Protocol: SFTP
- Robot IP
- Port: 22
- Logon type: Normal
    - user: root
    - password: easybot

Create a new folder in the program forder named "pyRobotiqGripperRTDE".

Paste the content of the "urController" folder of the package in the newly create folder.

Open a linux terminal on your PC. If you are using windows, open windows terminal and run wsl (Information on how to install wsl: https://learn.microsoft.com/en-us/windows/wsl/install).
The following instruction will run wsl from windows terminal:

.. code-block:: bash

    wsl

Access robot terminal using ssh. Replace <robot IP> by the IP of the robot.

.. code-block:: bash

    ssh root@<robot IP>

You will be prompted for the password. Which is: "easybot"

Navigate to the "pyRobotiqGripperRTDE" folder.

Excuse the following line to allow the execution of install.sh file:

.. code-block:: bash

    chmod +x install.sh

Then run the install.sh file. It will install all dependencies.

.. code-block:: bash

    ./install.sh

You can know run the python script which will start the RTDE register monitoring and control the gripper accordingly.

.. code-block:: bash

    python robotiqRTDE.py

The gripper will first activate before moving to the requested position written in RTDE register "input_int_register_24".

.. warning::

   Be aware that the register "input_int_register_24" maybe already used by a URCAP. Adjust the record_configuration.xml file and use the rtde_input_int_register option of the robotoiRTDE.py script to use a different RTDE register. 

Installation on realtime controller
-----------------------------------

The realtime controller is the PC from which are sent the realtime command to the robot. The realtime gripper control script of this package is just an example. It shows how to write gripper position in RTDE "input_int_register_24" request. If robotiqRTDE.py is running on the UR controller, the gripper will move to the position writen in the "input_int_register_24" RTDE register.

Copy the realtimeController folder of the package on your PC.

Open a terminal and navigate to the folder.

Create a python virtual environment (Make sure python 3 is installed: https://wiki.python.org/moin/BeginnersGuide/Download)

.. code-block:: bash

    python3 -m venv venv

Activate the virtual environment.

From windows:

.. code-block:: bash

    .\venv\Script\activate.bat

For linux:

.. code-block:: bash

    source venv/bin/activate

Install all dependencies:

.. code-block:: bash

    python3 -m pip install pygame UrRtde-2.7.12.tar.gz


Requirements:
=============

- If the PC is running windows: install wsl (https://learn.microsoft.com/en-us/windows/wsl/install)
- Install and run docker on the PC where you want to install the application (https://www.docker.com/get-started/)

Method A: Gripper connected at the wrist of the robot
============

.. code-block:: text

    Modbus TCP client  (500 Hz)
            |Modbus TCP command
            |Write gripper position request in register 0
            v
    Modbus TCP Server (500+ Hz)
            |Modbus RTU command (50hz)
            |Over ethernet
            v
    RS 485 URCAP (port 54321)
            |Modbus RTU command
            v
    Gripper at robot wrist

1- Install the RS485 URCAP on the UR robot. See the following documentation for instruction on how to install it:
https://github.com/UniversalRobots/Universal_Robots_ToolComm_Forwarder_URCap

2- Copy repository files in a folder on your PC.

3- Open a terminal and navigate to this folder.

4- Run docker command to build the docker image.

.. code-block:: bash

    docker build -t modbus-tcp-server:latest .

5- Run the docker image and pass the IP of the robot and the gripper Modbus id (default is 9). In the following example the robot IP is 10.0.0.80. When the docker image start, the gripper will open and close to complete its activation procedure. Make sure nothing interfer with the motion of the gripper.

.. code-block:: bash

    docker run --rm -t -p 502:502 modbus-tcp-server:latest --gripper_IP 10.0.0.80 --gripper_id 9 

By default the Modbus tcp server is accessible via 502 port. You can change for another port if you want. The following modification would give the Modbus tcp server accessible via 1050 port.
ex: -p 1050:502

6- Write realtime position request in Modbus tcp server register 0

Here below is an example of python script to send a position request to the Modbus TCP server.

.. code-block:: python

    from pymodbus.client import ModbusTcpClient
    client = ModbusTcpClient("127.0.0.1", port=502)
    client.connect()
    client.write_register(address=0, value=position)

Method B: Gripper connected to the PC serial port
============

.. code-block:: text

    Modbus TCP client  (500 Hz)
            |Modbus TCP command
            |Write gripper position request in register 0
            v
    Modbus TCP Server (500+ Hz)
            |Modbus RTU command (50hz)
            |Over PC serial
            v
    Gripper at PC serial port

1- Copy repository files in a folder on your PC.

2- Open a terminal and navigate to this folder.

3- Run docker command to build the docker image.

.. code-block:: bash

    docker build -t modbus-tcp-server:latest .

4- Only if the PC is running on windows:
- Install usbipd (https://github.com/dorssel/usbipd-win)
- Open window terminal ad administrator (right click on terminal application and select run as administrator)
- Excute the following command:

.. code-block:: bash

    usbipd list

This should return something like that :

.. code-block:: bash

    Connected:
    BUSID  VID:PID    DEVICE                                                        STATE
    2-1    0403:6015  USB Serial Converter                                          Attached
    2-3    2357:0604  TP-Link Bluetooth 5.3 USB Adapter                             Not shared
    2-5    0c45:6705  Integrated Webcam                                             Not shared
    2-7    04f3:0201  USB Input Device                                              Not shared
    3-6    8087:07dc  Intel(R) Wireless Bluetooth(R)                                Not shared

- Search for the busid of the usd device corresponding to the gripper. In this example "2-1".
- Share and attach the busid of the gripper with wsl using the following commant. Use the t1_ly identified busid.

.. code-block:: bash

    busipd bind --busid 2-1
    busipd attach --wsl --busid 2-1

4- In linux terminal (If the PC use window launch linux terminal by typing wsl in windows terminal) and search for gripper device name by copy and paste the following code in the terminal:

.. code-block:: bash

    {
    printf "%-15s %-20s %-25s %s\n" DEVICE VENDOR MODEL SERIAL
    for d in /dev/ttyUSB* /dev/ttyACM*; do
        [ -e "$d" ] || continue
        VENDOR=$(udevadm info -q property -n "$d" | sed -n 's/^ID_VENDOR=//p')
        MODEL=$(udevadm info -q property -n "$d" | sed -n 's/^ID_MODEL=//p')
        SERIAL=$(udevadm info -q property -n "$d" | sed -n 's/^ID_SERIAL=//p')
        printf "%-15s %-20s %-25s %s\n" "$d" "$VENDOR" "$MODEL" "$SERIAL"
    done
    }

You should see something like that:

.. code-block:: bash

    DEVICE          VENDOR               MODEL                     SERIAL
    /dev/ttyUSB0    FTDI                 USB_TO_RS-485             FTDI_USB_TO_RS-485_DA1P5HRO

5- Run the docker image and pass the t1_ly identified device name of the gripper. When the docker image start, the gripper will open and close to complete its activation procedure. Make sure nothing interfer with the motion of the gripper.

.. code-block:: bash

    docker run --rm -t --device=/dev/ttyUSB0:/dev/ttyUSB0 -p 502:502 modbus-tcp-server:latest --method "RTU" --gripper_id 9 --gripper_port "/dev/ttyUSB0"

By default the Modbus tcp server is accessible via 502 port. You can change for another port if you want. The following modification would give the Modbus tcp server accessible via 1050 port.
ex: -p 1050:502

5- Write realtime position request in Modbus tcp server register 0

Here below is an example of python script to send a position request to the Modbus TCP server.

.. code-block:: python

    from pymodbus.client import ModbusTcpClient
    client = ModbusTcpClient("127.0.0.1", port=502)
    client.connect()
    client.write_register(address=0, value=position)

Graphic interface to send pos command to TCP server for testing
============

If you add the option --hmi to the docker command it will run a graphic interface to send position command to the TCP server for testing. You can connect to this interface using a vnc client like realvnc (https://www.realvnc.com/en/connect/download/viewer/).
Connect to: localhost:5900

It runs a bit slow.

.. image:: modbusTCPgui.JPG
   :alt: Image of the graphic interface
   :width: 100%
   :align: center

You can run this interface faster by running it directly on your PC in a python virtual environment.
The following instructions works for Windows it would be similar commadns for Linux.

1- Install python3 on your PC: https://www.python.org/downloads/

2- Open the terminal and navigate to the "app" folder where is the "realtimeInterfaceTCP.py" file.

3- Create a virtual environment (Note that depending on the installation the way to call python3 may be different)

.. code-block:: bash

    python3 -m venv venv

4- Activate the environment

.. code-block:: bash

    .\venv\Script\activate.bat

5- Install depencies

.. code-block:: bash

    python3 -m pip install numpy pyqt5 scipy pymodbus pyqtgraph pyserial pygame

6- Run "realtimeInterfaceTCP.py"

.. code-block:: bash

    python3 realtimeInterfaceTCP.py

The concept
============

The application consist of:
- A Modbus TCP server which can recieve at high frequency position request (0-255) on its register 0
- A thread that monitor the position request saved in register 0 of the Modbus server and send appropriate command (position,speed,force) to the gripper connected at the wrist of the robot.

Both are packaged into a docker container to ease implementation.

The Modbus TCP server can receive position request at high frequency similar to UR RTDE (500Hz). So you can send realtime position request at 500Hz.

The thread, which is monitoring the position request, sends appropriate Modbus RTU command over serial port (method A) or ethernet to the UR robot ethernet port 54321 (method B).

The monitoring thread only forwards meaningful position requests. For example if the same position is requested at 500Hz the thread we send only 1 position request to the gripper. This prevent from overloading the gripper Modbus RTU communication which is not designed to handle high-frequency commands.

The gripper position request are processed by commandFilter.py. This script decide if the position have to be send to the gripper. It also set speed and force depending on the context.

Go further
============

It would be possible to integrate this control concept by making a URCAP which reads an RTDE register and send RTU command to the gripper connected at the wrist. RTDE is better suited for realtime control and RTU command are directly send to the gripper which would provide the smoothest communication.
The only draw back would be that such URCAP would ptentially load the robot controller processor and slow dow execution.

.. code-block:: text

    RTDE client  (500 Hz)
            |RTDE command
            |Over ethernet
            v
    RTDE to Modbus URCAP (50 Hz)
            |RTU commmad
            v
    Gripper at robot wrist

It would be also possible to communicate with the gripper connected at the wrist throught the Robotiq URCAP.
There is a fork for this approach: https://github.com/castetsb/pyRobotiqGripperRealTime/tree/ur_rtde_version

.. code-block:: text

    Modbus TCP client  (500 Hz)
            |Modbus TCP command
            |Write gripper position request in register 0
            v
    Modbus TCP Server (500+ Hz)
            |Robotiq URCAP server command
            |Over ethernet
            v
    Robotiq URCAP (50 Hz)
            |RTU command
            v
    Gripper at robot wrist

Joystick control
============
A script is available to try 3 different gripper control method using a joystick.
The following instructions works for Windows it would be similar commadns for Linux.

1- Install python3 on your PC: https://www.python.org/downloads/

2- Open the terminal and navigate to the "app" folder where is the "joystickControl.py" file.

3- (If you already created a virtual environment go to step 4) Create a virtual environment (Note that depending on the installation the way to call python3 may be different)

.. code-block:: bash

    python3 -m venv venv

4- Activate the environment

.. code-block:: bash

    .\venv\Script\activate.bat

5- Install depencies

.. code-block:: bash

    python3 -m pip install numpy pyqt5 scipy pymodbus pyqtgraph pyserial pygame

6- Run "joystickControl.py"

Example for "RTU" method:

.. code-block:: bash

    python3 joystickControl.py --gripper_port "COM8" --method "RTU"

Example for "RTU_VIA_TCP" method:

.. code-block:: bash

    python3 joystickControl.py --gripper_port 54321 --robot_ip 10.0.0.80 --method "RTU_VIA_TCP"

Example for "ROBOTIQ_URCAP" method:

.. code-block:: bash

    python3 joystickControl.py --gripper_port 63352 --robot_ip 10.0.0.80 --method "RTU_VIA_TCP"

"RTU" 
------------
The gripper is directly connected to a serial port of the PC.

.. code-block:: text

    Joystick (500 Hz)
            |[-1 1] analog signal
            v
    Python script (500 Hz)
            |Modbus RTU commands (50 Hz)
            |Over Serial Port
            v
    Gripper connected to PC serial

"RTU_VIA_TCP"
------------
The gripper is connected at the wrist of the robot. It is controlled with RTU command send over ethernet to RS485 URCAP at port 54321.

.. code-block:: text
    Joystick  (500 Hz)
            |[-1 1] analog signal
            v
    Python script (500 Hz)
            |Modbus RTU commands (50 Hz)
            |Over Ethernet
            v
    RS485 URCAP (500 Hz)
            |Modbus RTU commands (50 Hz)
            |Over Serial
            v
    Gripper connected at the wirst of the robot


"ROBOTIQ_URCAP"
------------
The gripper is connected at the wrist of the robot. It is controller with variable SET command send over ethernet to RObotiq URCAP at port 63352. 

.. code-block:: text

    Joystick  (500 Hz)
            |[-1 1] analog signal
            v
    Python script (500 Hz)
            |SET commands (50 Hz)
            |Over Ethernet
            v
    Robotiq URCAP (50 Hz)
            |Modbus RTU commands (50 Hz)
            |Over Serial
            v
    Gripper connected at the wirst of the robot====================
pyRobotiqGripperRTDE
====================

Introduction
============

This package provide software tools to control in a contious manner (realtime) a Robotiq gripper connected at the wrist of a UR robot from outside through RTDE.
The code have been tested on URSim with a 2F85 gripper.

The package is composed of 2 folders:

- urController: Software to deploy on UR controller which contains:
    - python2 dependencies packaged in tar.gz files
    - install.sh file to install dependencies
    - python2 script to monitor RTDE register and send appropriate commands to the gripper connected a thte wrist of the robot.
- realtimeController: Software to deploy on the PC from which the realtime gripper control is done. It contains:
    - urrtde package in tar.gz format
    - Example of python code which detect the position of a joystick and write the corresponding gripper position in RTDE register.

Installation
============
Installation on UR controller
-----------------------------
On UR the UR robot, setup the tool communication to be serial as below (I am not sure about the RX and TX settings).

.. image:: attachments/toolSerialSettings.JPG

Connect to the UR robot using a FTP client like Filezilla (https://filezilla-project.org/).
Default parameters to connect to robot FTP are the following:

- Protocol: SFTP
- Robot IP
- Port: 22
- Logon type: Normal
    - user: root
    - password: easybot

Create a new folder in the program forder named "pyRobotiqGripperRTDE".

Paste the content of the "urController" folder of the package in the newly create folder.

Open a linux terminal on your PC. If you are using windows, open windows terminal and run wsl (Information on how to install wsl: https://learn.microsoft.com/en-us/windows/wsl/install).
The following instruction will run wsl from windows terminal:

.. code-block:: bash

    wsl

Access robot terminal using ssh. Replace <robot IP> by the IP of the robot.

.. code-block:: bash

    ssh root@<robot IP>

You will be prompted for the password. Which is: "easybot"

Navigate to the "pyRobotiqGripperRTDE" folder.

Excuse the following line to allow the execution of install.sh file:

.. code-block:: bash

    chmod +x install.sh

Then run the install.sh file. It will install all dependencies.

.. code-block:: bash

    ./install.sh

You can know run the python script which will start the RTDE register monitoring and control the gripper accordingly.

.. code-block:: bash

    python robotiqRTDE.py

The gripper will first activate before moving to the requested position written in RTDE register "input_int_register_24".

.. warning::

   Be aware that the register "input_int_register_24" maybe already used by a URCAP. Adjust the record_configuration.xml file and use the rtde_input_int_register option of the robotoiRTDE.py script to use a different RTDE register. 

Installation on realtime controller
-----------------------------------

The realtime controller is the PC from which are sent the realtime command to the robot. The realtime gripper control script of this package is just an example. It shows how to write gripper position in RTDE "input_int_register_24" request. If robotiqRTDE.py is running on the UR controller, the gripper will move to the position writen in the "input_int_register_24" RTDE register.

Copy the realtimeController folder of the package on your PC.

Open a terminal and navigate to the folder.

Create a python virtual environment (Make sure python 3 is installed: https://wiki.python.org/moin/BeginnersGuide/Download)

.. code-block:: bash

    python3 -m venv venv

Activate the virtual environment.

From windows:

.. code-block:: bash

    .\venv\Script\activate.bat

For linux:

.. code-block:: bash

    source venv/bin/activate

Install all dependencies:

.. code-block:: bash

    python3 -m pip install pygame UrRtde-2.7.12.tar.gz

Connect a game controller to your PC.

Run the script which send controller position to RTDE register.

.. code-block:: bash

    python3 sendRTDE.py

Communication flow:
===================

.. code-block:: text

    Realtime controller
            |RTDE write command (500Hz)
            v
    Robot RTDE input_int_register_24
            |RTDE read command (about 60Hz)
            v
    robotiqRTDE.py
            |Modbus RTU command (about 60Hz)
            v
    Gripper at robot wrist

CAUTION
============

This application is a kind of prototype. It would need to be tested to make sure it is stable. Use at your own risks.
I hope the code of this application will help you to make your own realtime application.




CAUTION
============

This application is a kind of prototype. It would need to be tested to make sure it is stable. Use at your own risks.
I hope the code of this application will help you to make your own realtime application.