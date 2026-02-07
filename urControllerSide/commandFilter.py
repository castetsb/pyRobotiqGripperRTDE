
def sign(x):
    return (x > 0) - (x < 0)

def nextPosition(previousPos,previousPosRequest,previousSpeed,elapsedTime):
    """
    Evaluate next position from previous position, previous position request, previous speed request and elapsed time since previous request.
    """
    GRIPPER_VMAX = 332  # max speed in steps per second
    GRIPPER_VMIN = 68   # min speed in steps per second
    GRIPPER_BAUDRATE = 115200

    #Calculate predicted position
    previousPosDelta = previousPosRequest - previousPos
    
    previousDirection = sign(previousPosDelta)

    motion = int(previousDirection * float(GRIPPER_VMIN + (GRIPPER_VMAX - GRIPPER_VMIN) * previousSpeed / 255) * elapsedTime)
    
    newPos = 0
    
    if abs(previousPosDelta) < abs(motion):
        #Last position request was reachable within the elapsed time
        newPos = previousPosRequest
    else:
        #Last position was not reachable within elapsed time
        newPos = previousPos + motion
    
    if newPos<3 or previousPosRequest<3:
        #The gripper is fully open
        newPos=2
    if newPos>228 or previousPosRequest>228:
        #The gripper is fully closed
        newPos=229

    return newPos


def travelTime(currentPos,requestedPos,speed):
    GRIPPER_VMAX = 332  # max speed in steps per second
    GRIPPER_VMIN = 68   # min speed in steps per second
    posBitPerSecond = GRIPPER_VMIN + (float(GRIPPER_VMAX-GRIPPER_VMIN)/255)*speed
    timeToRequestedPos = abs(float(requestedPos-currentPos))/posBitPerSecond
    return timeToRequestedPos

def commandFilter(newPosRequest,newPosRequestTime,previousRequestTime,previousPos,previousPosRequest,previousSpeed,previousForce,minSpeedPosDelta=5,maxSpeedPosDelta=55):
    """
    Return the command that should be send to the gripper depending on a position request and previous command
    Execute the command just after this function.
    
    :param newPosRequest: Description
    :param previousRequestTime: Description
    :param previousPosRequest: Description
    :param previousSpeedRequest: Description
    :param previousForceRequest: Description
    """
    elapsedTime = newPosRequestTime-previousRequestTime

    command = {}

    command["toExecute"]=False
    command["currentPosition"]=0
    command["positionRequest"]=0
    command["speedRequest"]=0
    command["forceRequest"]=0
    command["waitTime"]=0

    newPos = nextPosition(previousPos,previousPosRequest,previousSpeed,elapsedTime)
    newSpeed = 0
    newForce = 0

    if abs(newPos - newPosRequest)>1:
        #The gripper is not at the requested position
        if newPosRequest <3 and previousPosRequest>=3:
            #Fully open request
            newSpeed = 255
            newForce = 255
            command["toExecute"]=True
            command["currentPosition"]=newPos
            command["positionRequest"]=0
            command["speedRequest"]=newSpeed
            command["forceRequest"]=newForce
            command["waitTime"]=travelTime(newPos,2,newSpeed)
        elif newPosRequest <3 and previousPosRequest<3:
            #Fully open request already executed
            newSpeed = 255
            newForce = 255
            command["toExecute"]=False
            command["currentPosition"]=newPos
            command["positionRequest"]=0
            command["speedRequest"]=newSpeed
            command["forceRequest"]=newForce
            command["waitTime"]=0

        elif newPosRequest >228 and previousPosRequest<=228:
            #Fully close
            newSpeed = 255
            newForce = 255
            command["toExecute"]=True
            command["currentPosition"]=newPos
            command["positionRequest"]=255
            command["speedRequest"]=newSpeed
            command["forceRequest"]=newForce
            command["waitTime"]=travelTime(newPos,229,newSpeed)
        elif newPosRequest >228 and previousPosRequest>228:
            #Fully close request already executed
            newSpeed = 255
            newForce = 255
            command["toExecute"]=False
            command["currentPosition"]=newPos
            command["positionRequest"]=255
            command["speedRequest"]=newSpeed
            command["forceRequest"]=newForce
            command["waitTime"]=0

        else:
            #newPosRequest >=3 and newPosRequest <=228:
            if (previousPosRequest<3 or previousPosRequest>228):
                #Release from ends stop
                newSpeed = 255
                newForce = 255
                command["toExecute"]=True
                command["currentPosition"]=newPos
                command["positionRequest"]=newPosRequest
                command["speedRequest"]=newSpeed
                command["forceRequest"]=newForce
                command["waitTime"]=travelTime(newPos,newPosRequest,newSpeed)
            else:
                #Moving within motion range

                #New speed calculation
                newSpeed = 0
                posDelta = abs(newPosRequest - newPos)
                if posDelta <= minSpeedPosDelta:
                    #Requested position is close from current position. The speed is slow.
                    newSpeed = 0
                elif posDelta > maxSpeedPosDelta:
                    #Requested position is fare from the current position. The speed is fast.
                    newSpeed = 255
                else:
                    #Request is a bit distant. The speed increase with the distance between current position and requested position.
                    newSpeed = int((float(posDelta - minSpeedPosDelta) /(maxSpeedPosDelta - minSpeedPosDelta)) * 255
)
                    print(((posDelta - minSpeedPosDelta)/(maxSpeedPosDelta - minSpeedPosDelta))*255)
                
                newForce=0

                if (previousPos == newPosRequest) and (previousSpeed == newSpeed) and (previousForce == newForce):
                    #Previous command was identical as new command. We do nothing.
                    command["toExecute"]=False
                    command["currentPosition"]=newPos
                    command["positionRequest"]=newPosRequest
                    command["speedRequest"]=newSpeed
                    command["forceRequest"]=newForce
                    command["waitTime"]=0
                else:
                    command["toExecute"]=True
                    command["currentPosition"]=newPos
                    command["positionRequest"]=newPosRequest
                    command["speedRequest"]=newSpeed
                    command["forceRequest"]=newForce
                    command["waitTime"]=0
                    
    else:
        #The gripper is at the requested position
        newSpeed=0
        newForce=0
        command["toExecute"]=False
        command["currentPosition"]=newPos
        command["positionRequest"]=newPosRequest
        command["speedRequest"]=newSpeed
        command["forceRequest"]=newForce
        command["waitTime"]=0
    
    return command


