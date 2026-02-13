from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import time

GRIPPER_BAUDRATE = 115200
GRIPPER_MODE_RTU_VIA_TCP = "RTU_VIA_TCP"
GRIPPER_MODE_RTU = "RTU"

class Gripper(ModbusClient):

    def __init__(self, port, device_id=9):
        ModbusClient.__init__(self,method='rtu',
                       port=port,   # or COM3 on Windows
                       baudrate=115200,
                       parity='N',
                       stopbits=1,
                       bytesize=8,
                       timeout=1)
        self.device_id = device_id

    def activate_gripper(self):
        position=int(0)
        speed=int(255)
        force=int(0)
        res=self.write_registers(address=1000,
                                 values=[0,0,0],
                                 unit=self.device_id)
        res=self.write_registers(address=1000,
                                 values=[0b0000100100000000,position,speed * 0b100000000 + force],
                                 unit=self.device_id)

        # Check result
        if res.isError():
            print "Activation failed"
        time.sleep(3)

    def writePSF(self,position, speed, force):
        res=self.write_registers(address=1001,
                                 values=[position,speed * 0b100000000 + force],
                                 unit=self.device_id)

        # Check result
        if res.isError():
            print "Write failed"
    
    def readStatus(self):
        result=self.read_holding_registers(address=2000,
                                           count=3,
                                           unit=self.device_id)
        registers=result.registers
        paramDic={}
        #########################################
        #Register 2000
        #First Byte: gripperStatus
        #Second Byte: RESERVED
        
        #First Byte: gripperStatus
        gripperStatusReg0=(registers[0] >> 8) & 0b11111111 #xxxxxxxx00000000
        #########################################
        #Object detection
        paramDic["gOBJ"]=(gripperStatusReg0 >> 6) & 0b11 #xx000000
        #Gripper status
        paramDic["gSTA"]=(gripperStatusReg0 >> 4) & 0b11 #00xx0000
        #Action status. echo of rGTO (go to bit)
        paramDic["gGTO"]=(gripperStatusReg0 >> 3) & 0b1 #0000x000
        #Activation status
        paramDic["gACT"]=gripperStatusReg0 & 0b00000001 #0000000x
        
        #########################################
        #Register 2001
        #First Byte: Fault status
        #Second Byte: Pos request echo
        
        #First Byte: fault status
        faultStatusReg2= (registers[1] >>8)  & 0b11111111 #xxxxxxxx00000000
        #########################################
        #Universal controler
        paramDic["kFLT"]=(faultStatusReg2 >> 4) & 0b1111 #xxxx0000
        #Fault
        paramDic["gFLT"]=faultStatusReg2 & 0b00001111 #0000xxxx
        
        
        #########################################
        #Second Byte: Pos request echo
        posRequestEchoReg3=registers[1] & 0b11111111 #00000000xxxxxxxx
        #########################################
        #Echo of request position
        paramDic["gPR"]=posRequestEchoReg3
        
        #########################################
        #Register 2002
        #First Byte: Position
        #Second Byte: Current
        
        #First Byte: Position
        positionReg4=(registers[2] >> 8) & 0b11111111 #xxxxxxxx00000000

        #########################################
        #Actual position of the gripper
        paramDic["gPO"]=positionReg4
        
        #########################################
        #Second Byte: Current
        currentReg5=registers[2] & 0b0000000011111111 #00000000xxxxxxxx
        #########################################
        #Current
        paramDic["gCU"]=currentReg5

        return paramDic

    def writePSFreadStatus(self,position, speed, force):
        result=self.readwrite_registers(read_address=2000,
                                        read_count=3,
                                        write_address=1001,
                                        write_registers=[position, speed * 0b100000000 + force],
                                        unit=self.device_id)
        registers=result.registers
        paramDic={}
        #########################################
        #Register 2000
        #First Byte: gripperStatus
        #Second Byte: RESERVED
        
        #First Byte: gripperStatus
        gripperStatusReg0=(registers[0] >> 8) & 0b11111111 #xxxxxxxx00000000
        #########################################
        #Object detection
        paramDic["gOBJ"]=(gripperStatusReg0 >> 6) & 0b11 #xx000000
        #Gripper status
        paramDic["gSTA"]=(gripperStatusReg0 >> 4) & 0b11 #00xx0000
        #Action status. echo of rGTO (go to bit)
        paramDic["gGTO"]=(gripperStatusReg0 >> 3) & 0b1 #0000x000
        #Activation status
        paramDic["gACT"]=gripperStatusReg0 & 0b00000001 #0000000x
        
        #########################################
        #Register 2001
        #First Byte: Fault status
        #Second Byte: Pos request echo
        
        #First Byte: fault status
        faultStatusReg2= (registers[1] >>8)  & 0b11111111 #xxxxxxxx00000000
        #########################################
        #Universal controler
        paramDic["kFLT"]=(faultStatusReg2 >> 4) & 0b1111 #xxxx0000
        #Fault
        paramDic["gFLT"]=faultStatusReg2 & 0b00001111 #0000xxxx
        
        
        #########################################
        #Second Byte: Pos request echo
        posRequestEchoReg3=registers[1] & 0b11111111 #00000000xxxxxxxx
        #########################################
        #Echo of request position
        paramDic["gPR"]=posRequestEchoReg3
        
        #########################################
        #Register 2002
        #First Byte: Position
        #Second Byte: Current
        
        #First Byte: Position
        positionReg4=(registers[2] >> 8) & 0b11111111 #xxxxxxxx00000000

        #########################################
        #Actual position of the gripper
        paramDic["gPO"]=positionReg4
        
        #########################################
        #Second Byte: Current
        currentReg5=registers[2] & 0b0000000011111111 #00000000xxxxxxxx
        #########################################
        #Current
        paramDic["gCU"]=currentReg5

        return paramDic
    
    
    def writeP(self,position):
        res=self.write_registers(address=1001,
                                 values=[position],
                                 unit=self.device_id)

        # Check result
        if res.isError():
            print "Write failed"

    def writeSF(self,speed, force):
        res=self.write_registers(address=1002,
                                 values=[speed * 0b100000000 + force],
                                 unit=self.device_id)

        # Check result
        if res.isError():
            print "Write failed"

    def waitComplete(self, timeout=5.0):
        gOBJ=0b00
        while gOBJ == 0b00 and (time.time() - startTime) < timeout:
            result=self.read_holding_registers(address=2000,
                                               count=1,
                                               unit=self.device_id)
            registers=result.registers
            gripperStatusReg0=(registers[0] >> 8) & 0b11111111
            gOBJ=(gripperStatusReg0 >> 6) & 0b11
    
    def estimateAndWaitComplete(self,currentPos,requestedPos,speed):
        GRIPPER_VMAX = 332  # max speed in steps per second
        GRIPPER_VMIN = 68   # min speed in steps per second
        posBitPerSecond = GRIPPER_VMIN + ((GRIPPER_VMAX-GRIPPER_VMIN)/255)*speed
        timeToRequestedPos = abs(requestedPos-currentPos)/posBitPerSecond
        time.sleep(timeToRequestedPos)



    def currentPos(self):
        result=self.read_holding_registers(address=2002,
                                           count=1,
                                           unit=self.device_id)
        registers=result.registers
        position=(registers[0] >> 8) & 0b11111111 #xxxxxxxx00000000
        return position

#test MODE RTU
if False:
    gripper = Gripper("COM8")
    if not gripper.connect():
        print("Unable to connect")
        exit(1)
    print("activation")
    gripper.activate_gripper()
    time.sleep(2)
    print("write P")
    gripper.writeP(100)
    time.sleep(1)
    gripper.writePSF(150,200,200)
    time.sleep(1)


    status=gripper.readStatus()
    print(status)
    status=gripper.writePSFreadStatus(200,255,255)
    print(status)

