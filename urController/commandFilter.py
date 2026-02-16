
def sign(x):
    return (x > 0) - (x < 0)

def nextPosition(t1_Pos,t1_PosRequest,t1_Speed,elapsedTime):
    """
    Evaluate next position from t1_ position, t1_ position request, t1_ speed request and elapsed time since t1_ request.
    """
    GRIPPER_VMAX = 332  # max speed in steps per second
    GRIPPER_VMIN = 68   # min speed in steps per second

    #Calculate predicted position
    t1_PosDelta = t1_PosRequest - t1_Pos
    
    t1_Direction = sign(t1_PosDelta)

    motion = int(t1_Direction * float(GRIPPER_VMIN + (GRIPPER_VMAX - GRIPPER_VMIN) * t1_Speed / 255) * elapsedTime)
    
    t0_Pos = 0
    
    if abs(t1_PosDelta) < abs(motion):
        #Last position request was reachable within the elapsed time
        t0_Pos = t1_PosRequest
    else:
        #Last position was not reachable within elapsed time
        t0_Pos = t1_Pos + motion

    return t0_Pos


def bitPerSecond(speed):
    GRIPPER_VMAX = 332  # max speed in steps per second
    GRIPPER_VMIN = 68   # min speed in steps per second
    res=GRIPPER_VMIN + (float(GRIPPER_VMAX-GRIPPER_VMIN)/255)*speed
    return res


def travelTime(currentPos,requestedPos,speed):
    GRIPPER_VMAX = 332  # max speed in steps per second
    GRIPPER_VMIN = 68   # min speed in steps per second
    posBitPerSecond = bitPerSecond(speed)
    timeToRequestedPos = abs(float(requestedPos-currentPos))/posBitPerSecond
    return timeToRequestedPos

def listIdValueUnderThreshold(lst,threshold):
    i=0
    lstId=0
    found=False
    while i<len(lst) and not found:
        if lst[i]<threshold:
            lstId=i
            found=True
        i+=1
    if not found:
        raise Exception("Could not find value under {} in {}".format(threshold,lst))
    return lstId

def listSubstract(lst,value):
    for i in range(len(lst)):
        lst[i] -= value

def areValueIdentical(lst):
    value = lst[0]
    res=True
    i=0
    while i<len(lst):
        if lst[i]!=value:
            res=False
        i+=1
    return res

def commandInElapsedTime(commandHistory,elaspedTime):
    elaspedTimeHistory=[x - commandHistory["time"][0] for x in commandHistory["time"]]
    inElapsedTimeId=listIdValueUnderThreshold(elaspedTimeHistory,elaspedTime)
    commands=commandHistory.copy()
    if inElapsedTimeId is None or inElapsedTimeId<2:
        for key,value in commands.items():
            commands[key]=commands[key][:2]
    else:
        for key,value in commands.items():
            commands[key]=commands[key][:inElapsedTimeId]
    #print(commandHistory)
    #print(commands)
    
    return commands

def objectDetected(commandHistory):
    NO_OBJECT_DETECTED = 0
    
    OBJECT_DETECTED_WHILE_OPENING = 1
    OBJECT_DETECTED_WHILE_CLOSING = 2

    COM_TIME = 0.016

    res=NO_OBJECT_DETECTED

    #If position is identical for more than 20x0.016s (time to move of 20 bits)
    #print(commandHistory)
    timeThresholdId=listIdValueUnderThreshold(commandHistory["time"],commandHistory["time"][0]-COM_TIME*25)
    if timeThresholdId<2:
        timeThresholdId=2
    #commands = commandInElapsedTime(commandHistory,COM_TIME*20)
    
    isImobile = areValueIdentical(commandHistory["position"][:timeThresholdId])
    if isImobile:

        if (min(commandHistory["positionCommand"][:timeThresholdId]) - commandHistory["position"][0]) > 0:
            res=OBJECT_DETECTED_WHILE_CLOSING
        elif (max(commandHistory["positionCommand"][:timeThresholdId]) - commandHistory["position"][0] )<0:
            res=OBJECT_DETECTED_WHILE_OPENING
        else:
            res=NO_OBJECT_DETECTED
    
    return res

def updateList(data,value):
    data[1:]=data[:-1]
    data[0]=value


def commandFilter(t0_RequestTime,
                  t0_RequestPosition,
                  commandHistory,
                  statusUpdate,
                  minSpeedPosDelta=5,
                  maxSpeedPosDelta=55,
                  continuousGrip=True,
                  autoLock=True,
                  minimalMotion=1):
    NO_OBJECT_DETECTED = 0
    
    OBJECT_DETECTED_WHILE_OPENING = 1
    OBJECT_DETECTED_WHILE_CLOSING = 2

    #Object detection
    t1_CommandDetection =NO_OBJECT_DETECTED
    
    if (statusUpdate is None) :
        t1_CommandDetection = objectDetected(commandHistory)
    elif (statusUpdate["time"]<commandHistory["time"][0]):
        t1_CommandDetection = objectDetected(commandHistory)
    else:        
        #print("Detection from status")
        t1_CommandDetection = statusUpdate["gOBJ"]
    
    GRIP_NOT_REQUESTED = 0
    GRIP_REQUESTED = 1
    GRIP_VALIDATED = 2

    OBJECT_DETECTED_DURING_OPENING = 1
    OBJECT_DETECTED_DURING_CLOSING = 2

    GRIPPER_VMAX = 332  # max speed in steps per second
    GRIPPER_VMIN = 68   # min speed in steps per second

    NO_COMMAND =0
    WRITE_READ_COMMAND = 1
    READ_COMMAND = 2

    COM_TIME = 0.016

    elapsedTime = t0_RequestTime-commandHistory["time"][0]
    forceMin = continuousGrip*1
    command = {}

    command["execution"]=NO_COMMAND
    command["position"]=0
    command["speed"]=0
    command["force"]=forceMin
    command["grip"]=GRIP_NOT_REQUESTED
    command["wait"]=0
    
    t0_CalculatedPosition = nextPosition(commandHistory["position"][0],commandHistory["positionCommand"][0],commandHistory["speedCommand"][0], elapsedTime)

    if (t1_CommandDetection == OBJECT_DETECTED_DURING_OPENING) and autoLock:

        #An object have been detected during opening
        if commandHistory["gripCommand"][0]==GRIP_NOT_REQUESTED:
            #The gripper has not been request to grip
            if (t0_RequestPosition <= commandHistory["position"][0]):
                #Secure the grip
                command["execution"]=WRITE_READ_COMMAND
                command["position"]=0
                command["speed"]=255
                command["force"]=255
                command["grip"]=GRIP_REQUESTED
                command["wait"]=travelTime(0,10,GRIPPER_VMAX)
            else:
                #Release
                command["execution"]=WRITE_READ_COMMAND
                command["position"]=t0_RequestPosition
                command["speed"]=255
                command["force"]=255
                command["grip"]=GRIP_NOT_REQUESTED
                command["wait"]=travelTime(t0_CalculatedPosition,t0_RequestPosition,255)
        elif commandHistory["gripCommand"][0]==GRIP_REQUESTED:
            #The gripper has been requested to grip. Final grip position is unknown.
            if t0_RequestPosition <= commandHistory["position"][0]:
                #The position is inside the grip
                #Validate the grip
                command["execution"]=READ_COMMAND
                command["position"]=None
                command["speed"]=None
                command["force"]=None
                command["grip"]=None
                command["wait"]=None
            else:
                #The position is ouside the grip
                #Release
                command["execution"]=WRITE_READ_COMMAND
                command["position"]=t0_RequestPosition
                command["speed"]=255
                command["force"]=255
                command["grip"]=GRIP_NOT_REQUESTED
                command["wait"]=travelTime(t0_CalculatedPosition,t0_RequestPosition,255)
        else:
            #GRIP_VALIDATED

            if t0_RequestPosition <= commandHistory["position"][0]:
                #The position is inside the grip
                #Validate the grip
                command["execution"]=READ_COMMAND
                command["position"]=0
                command["speed"]=0
                command["force"]=0
                command["grip"]=0
                command["wait"]=0
            else:
                #The position is ouside the grip
                #Release
                command["execution"]=WRITE_READ_COMMAND
                command["position"]=t0_RequestPosition
                command["speed"]=255
                command["force"]=255
                command["grip"]=0
                command["wait"]=travelTime(commandHistory["position"][0],t0_RequestPosition,t0_Speed)

    elif t1_CommandDetection == OBJECT_DETECTED_DURING_CLOSING and autoLock:
        #print("Object detected while closing")
        #An object have been detected during closing
        if commandHistory["gripCommand"][0]==GRIP_NOT_REQUESTED:
            #The gripper has not been request to grip
            if t0_RequestPosition >= commandHistory["position"][0]:
                #Secure the grip
                command["execution"]=WRITE_READ_COMMAND
                command["position"]=255
                command["speed"]=255
                command["force"]=255
                command["grip"]=GRIP_REQUESTED
                command["wait"]=travelTime(0,10,GRIPPER_VMAX)
            else:
                #Release
                command["execution"]=WRITE_READ_COMMAND
                command["position"]=t0_RequestPosition
                command["speed"]=255
                command["force"]=255
                command["grip"]=GRIP_NOT_REQUESTED
                command["wait"]=travelTime(t0_CalculatedPosition,t0_RequestPosition,255)
        elif commandHistory["gripCommand"][0]==GRIP_REQUESTED:
            #The gripper has been requested to grip. Final grip position is unknown.
            if t0_RequestPosition >= commandHistory["position"][0]:
                #The position is inside the grip
                #Validate the grip
                command["execution"]=READ_COMMAND
                command["position"]=None
                command["speed"]=None
                command["force"]=None
                command["grip"]=None
                command["wait"]=None
            else:
                #The position is ouside the grip
                #Release
                command["execution"]=WRITE_READ_COMMAND
                command["position"]=t0_RequestPosition
                command["speed"]=255
                command["force"]=255
                command["grip"]=0
                command["wait"]=travelTime(t0_CalculatedPosition,t0_RequestPosition,255)
        else:
            #GRIP_VALIDATED

            if t0_RequestPosition >= commandHistory["position"][0]:
                #The position is inside the grip
                #Validate the grip
                command["execution"]=READ_COMMAND
                command["position"]=0
                command["speed"]=0
                command["force"]=0
                command["grip"]=0
                command["wait"]=0
            else:
                #The position is ouside the grip
                #Release
                command["execution"]=WRITE_READ_COMMAND
                command["position"]=t0_RequestPosition
                command["speed"]=255
                command["force"]=255
                command["grip"]=0
                command["wait"]=travelTime(t0_CalculatedPosition,t0_RequestPosition,255)

    else:
        if abs(commandHistory["positionCommand"][0]-t0_RequestPosition)>minimalMotion:
            if t0_RequestPosition==0 or t0_RequestPosition==255:
                command["execution"]=WRITE_READ_COMMAND
                command["position"]=t0_RequestPosition
                command["speed"]=255
                command["force"]=255
                command["grip"]=GRIP_NOT_REQUESTED
                command["wait"]=travelTime(t0_CalculatedPosition,t0_RequestPosition,255)
            else:
                #Move only if request is distant of 2 bits to avoid having the gripper checking between 2 positions.

                #t0_ speed calculation
                t0_Speed = 0
                posDelta = abs(t0_RequestPosition - t0_CalculatedPosition)
                if posDelta <= minSpeedPosDelta:
                    #Requested position is close from current position. The speed is slow.
                    t0_Speed = 0
                elif posDelta > maxSpeedPosDelta:
                    #Requested position is fare from the current position. The speed is fast.
                    t0_Speed = 255
                else:
                    #Request is a bit distant. The speed increase with the distance between current position and requested position.
                    t0_Speed = int((float(posDelta - minSpeedPosDelta) /(maxSpeedPosDelta - minSpeedPosDelta)) * 255)
                if (commandHistory["positionCommand"][0] == t0_RequestPosition) and (commandHistory["speedCommand"][0] == t0_Speed) and (commandHistory["forceCommand"][0] == t0_Force):
                    #t1_ command was identical as t0_ command. We do nothing.
                    command["execution"]=READ_COMMAND
                    command["position"]=None
                    command["speed"]=None
                    command["force"]=None
                    command["grip"]=None
                    command["wait"]=None
                else:
                    command["execution"]=WRITE_READ_COMMAND
                    command["position"]=t0_RequestPosition
                    command["speed"]=t0_Speed
                    command["force"]=forceMin
                    command["grip"]=GRIP_NOT_REQUESTED
                    command["wait"]=0#travelTime(0,2,t0_Speed)
        else:
            command["execution"]=READ_COMMAND
            command["position"]=None
            command["speed"]=None
            command["force"]=None
            command["grip"]=None
            command["wait"]=None
    
    return command