import time
import math
from subprocess import call

from parser import Parser
from driveController import DriveController
from cameraTower import Camera

def wallDrive(parser: Parser, dC: DriveController, dir, speedCurve, speedStraight, angle = 45, i = 0):
    if i == 3:
        dist = 600
    else:
        dist = 350
    
    
    if angle == 45:
        dist += 100
        if dir == dC.rightWall:
            wall = dC.angleRightWall
        else:
            wall = dC.angleLeftWall
            angle = -angle
        
    elif angle == 90:
        if dir == dC.rightWall:
            wall = dC.rightWall
        else:
            wall = dC.leftWall
            angle = -angle

    dC.turn(speedCurve,angle)
    dC.driveToWall(speedStraight,angle,dist,wall)
    dC.turn(speedCurve,0)
    # dC.driveToWall(speedStraight,0,1000,wall)
    
    if dir == dC.convertDir(parser, dC.leftWall):
        wallLost = dC.driveToWall(speedStraight,0,1100,900,avoidWall=dC.convertDir(parser, dC.leftWall))
        # drove to far (past the next obstacle):
        if wallLost and parser.checkSectionAuto(dC.nextSection()) == parser.GREEN:
            dC.brake()
            dC.driveDist(-1,0,510)
            dC.brake()
    else:
        dC.driveToWall(speedStraight,0,1050, 900, avoidWall=None)
    
def unParkCW(parser: Parser, dC: DriveController):
    speedStraight=1
    speedCurve=1
    speedCurveSlow=0.6
    sectionObstacleList = parser.checkSectionMulti(dC.section, True)
    print("First obstacle: " + str(sectionObstacleList[0]) + ", second obsacle: " + str(sectionObstacleList[1]))
    if sectionObstacleList[0] == parser.GREEN:
        dC.tightTurn(speedCurveSlow, -40)
        dC.driveDist(speedStraight, -40, 200)
        dC.turn(speedCurve, 0)
        dC.driveToWall(speedStraight,0,1050, 900, minTravel=500)
    else:
        dC.tightTurn(speedCurveSlow, -90)
        # dC.driveDist(speedStraight, -40, 200)
        dC.driveToWall(speedStraight,-90,300, 0)
        dC.turn(speedCurve, 0)
        dC.driveToWall(speedStraight,0,1050, 900)

def unParkCCW(parser: Parser, dC: DriveController):
    speedStraight=1
    speedStraightSlow=0.6
    speedCurve=1
    speedCurveSlow=0.6
    
    sectionObstacleList = parser.checkSectionMulti(dC.section)
    print("First obstacle: " + str(sectionObstacleList[0]) + ", second obsacle: " + str(sectionObstacleList[1]))
    if sectionObstacleList[1] == parser.RED:
        dC.tightTurn(speedCurveSlow, -40)
        dC.driveDist(speedStraight, -40, 350)
    else:
        dC.tightTurn(speedCurveSlow, -90)
        dC.driveToWall(speedStraightSlow,-90,300, 0)
        dC.brake()
        dC.tightTurn(speedCurveSlow, 0)

def parkCW(parser: Parser, dC: DriveController):
    speedStraight=1
    speedStraightSlow=0.6
    speedStraightVerySlow=0.3
    speedCurve=1
    speedCurveSlow=0.6
    
    sectionObstacleList = parser.checkSectionMulti(dC.section, True)
    prevSectionObstacleList = parser.checkSectionMulti(dC.prevSection(), True)
    
    print("First obstacle: " + str(sectionObstacleList[0]) + ", second obsacle: " + str(sectionObstacleList[1]))
    
    dC.brake()
    if sectionObstacleList[1] == parser.RED:
        dC.driveToWall(speedStraightVerySlow,90,800,dC.frontWall)
        dC.brake()
        dC.tightTurn(speedCurveSlow,0)
        dC.brake()
        if prevSectionObstacleList[1] == parser.GREEN:
            dC.driveDist(speedStraightSlow, 0, 300)
        dC.driveToWall(speedStraightVerySlow, 0, 180, wallDir=dC.leftWall)
        dC.driveDist(speedStraightSlow, 0, 150)
        dC.brake()
        dC.tightTurn(speedCurveSlow,-45)
        dC.brake()
        dC.tightTurn(-speedCurveSlow,-70)
        dC.brake()
        dC.tightTurn(speedCurveSlow,-90)
        dC.brake()
        dC.driveDist(-speedStraightSlow, -90, 300)
        dC.driveToWall(-speedStraightSlow, -90, 300, wallDir=dC.backWall)
        dC.brake()
        dC.tightTurn(-speedCurveSlow, 0)
        dC.brake()
    else:
        dC.driveToWall(speedStraightSlow,90,400,dC.frontWall)
        dC.brake()
        dC.tightTurn(speedCurveSlow,0)
        dC.brake()
        if prevSectionObstacleList[1] == parser.GREEN:
            dC.driveDist(speedStraightSlow, 0, 300)
        dC.driveToWall(speedStraightVerySlow, 0, 180, wallDir=dC.leftWall)
        dC.driveDist(speedStraightVerySlow, 0, 150)
        dC.brake()
        dC.tightTurn(speedCurveSlow, -90)
        dC.brake()
        dC.driveToWall(-speedStraightSlow, -90, 300, wallDir=dC.backWall)
        dC.brake()
        dC.tightTurn(-speedCurveSlow, 0)
        dC.brake()

def parkCCW(parser: Parser, dC: DriveController, sectionObstacleList):
    speedStraight=1
    speedStraightSlow=0.6
    speedStraightVerySlow=0.3
    speedCurve=1
    speedCurveSlow=0.6
    
    print("First obstacle: " + str(sectionObstacleList[0]) + ", second obsacle: " + str(sectionObstacleList[1]))
    dC.brake()
    if sectionObstacleList[0] == parser.GREEN:
        dC.tightTurn(speedCurveSlow,90)
        dC.driveToWall(speedStraightSlow,90,400,dC.frontWall)
        dC.tightTurn(speedCurveSlow,0)
    # else:
    dC.driveDist(speedStraight, 0, 500)
    dC.brake()
    dC.tightTurn(speedCurveSlow, 0)
    dC.driveToWall(speedStraightSlow,0,1050, 900)
    dC.brake()
    dC.driveDist(-speedStraightSlow, 0, 100)
    dC.brake()
    dC.driveToWall(-speedStraightVerySlow, 0, 180, wallDir=dC.rightWall)
    dC.brake()
    dC.driveDist(speedStraightSlow, 0, 150)
    dC.brake()
    dC.tightTurn(speedCurveSlow, -90)
    dC.brake()
    dC.driveToWall(-speedStraightSlow, -90, 300, wallDir=dC.backWall)
    dC.brake()
    dC.tightTurn(-speedCurveSlow, 0)
    dC.brake()

def detectObstaclesCCW(parser: Parser, cam: Camera):
    parser.setTowerAngle(270)
    cam.captureImage()
    cam.getObstacles("CCW", 0)
    call("sudo systemctl restart smbd", shell=True)
    

def findDirection(parser: Parser, dC: DriveController):
    distRight = 0
    distLeft = 0
    
    while (distLeft > 400 or distLeft == 0) and (distRight > 400 or distRight == 0):
        distRight = dC.getDist([3,4],3,dC.rightWall)
        distLeft = dC.getDist([3,4],3,dC.leftWall)
    
    print(f"Distance right: {distRight}, Distance left: {distLeft}")
    dC.logger.log(f"Obstacel Challenge Single Distance right: {distRight}, Distance left: {distLeft}")
    dC.logger.logTof(parser, parser.leftSensor)
    dC.logger.logTof(parser, parser.rightSensor)
    
    
    if distRight >0 and distRight < 400:
        print("counterClockwise")
        dC.logger.log("Obstacle Challenge: counterClockwise")
        parser.Direction = parser.CCW
    else:
        print("Clockwise")
        dC.logger.log("Obstacle Challenge: clockwise")
        parser.Direction = parser.CW

def FirstObstacle(parser: Parser, dC: DriveController, sectionObstacleList, i):
    speedStraight = dC.topSpeed
    speedCurve=1
    
    if i == 3:
        wallDriveDist = 600
    else:
        wallDriveDist = 450
        
    print("Obstacle:", parser.colorName(parser.checkSection(dC.section)))
    
    if sectionObstacleList[0] == parser.GREEN:
        dC.turn(speedCurve,0)
        dC.driveAwayFromWall(speedStraight, 0, 1000)
        
    elif sectionObstacleList[0] in (parser.RED, None):
        print(f"Color thingy: {parser.colorName(parser.checkSection(dC.prevSection()))}")
        dC.driveToWall(speedStraight,90,wallDriveDist)
        dC.turn(speedCurve,0)
        dC.driveAwayFromWall(speedStraight, 0, 1000)

def SameObstacles(parser: Parser, dC: DriveController, sectionObstacleList):
    speedStraight = dC.topSpeed
    
    if sectionObstacleList[0] == parser.GREEN:
        wallLost = dC.driveToWall(speedStraight,0,1100,900,avoidWall=dC.leftWall,minTravel=750)
        # drove to far (past the next obstacle):
        if wallLost and parser.checkSection(dC.nextSection(), True) == parser.GREEN:
            dC.brake()
            dC.driveDist(-1,0,510)
            dC.brake()

    elif sectionObstacleList[0] in (parser.RED, None):
        dC.driveToWall(speedStraight,0,1050, 900, avoidWall=None, minTravel=750)

def SecondObstacle(parser: Parser, dC: DriveController, sectionObstacleList, i):
    speedStraight = dC.topSpeed
    speedCurve=1
    
    if sectionObstacleList[0] == parser.GREEN and sectionObstacleList[1] == parser.RED:
        dC.driveDist(speedStraight, 0, 300)
        wallDrive(parser, dC, dC.rightWall, speedCurve, speedStraight, 90, i)
    
    else: # Red -> Green
        dC.driveDist(speedStraight, 0, 300)
        wallDrive(parser, dC, dC.leftWall, speedCurve, speedStraight, 90)

def obstacleChallenge(parser: Parser, dC: DriveController, cam: Camera):
    speedStraight = dC.topSpeed
    speedCurve=1
    speedCurveSlow=0.65
    
    parser.obstacles[0] = parser.RED
    parser.obstacles[2] = parser.RED
    
    parser.obstacles[3] = parser.RED
    parser.obstacles[5] = parser.RED
    
    parser.obstacles[6] = parser.RED
    parser.obstacles[8] = parser.RED
    
    parser.obstacles[9] = parser.RED
    parser.obstacles[11] = parser.RED
    
    findDirection(parser, dC)
    mirror = False
    if parser.Direction == parser.CW:
        mirror = True
        unParkCW(parser, dC)
    else:
        mirror = False
        unParkCCW(parser, dC)
    
    dC.section += 1
    for j in range(3):
        for i in range(4):
            lastSection = i == 3 and j == 2
            secondToLastSection = i == 2 and j == 2
            sectionObstacleList = parser.checkSectionMulti(dC.section, mirror, mirror)
            parked = False
            
            if secondToLastSection and parser.Direction == parser.CW:
                dC.topSpeed = 1
             
            if lastSection and parser.Direction == parser.CW:
                parkCW(parser, dC)
                parked = True
            else:
                FirstObstacle(parser, dC, sectionObstacleList, i)
                if lastSection:
                    parkCCW(parser, dC, sectionObstacleList)
                    parked = True
            
            if sectionObstacleList[0] == sectionObstacleList[1] and not parked:
                SameObstacles(parser, dC, sectionObstacleList)
            elif not parked:
                SecondObstacle(parser, dC, sectionObstacleList, i)
            
            dC.section = dC.nextSection()
            
            if dC.end():
                print("\n--------------------- END --------------------\n")
                return
            
            print("!!!!!!!!!!!!!!!!!!!!! DONE !!!!!!!!!!!!!!!!!!!!")
        parser.round += 1
        print("********************* Super DONE ********************")
    
    parser.endTime = time.time()
    dC.brake()