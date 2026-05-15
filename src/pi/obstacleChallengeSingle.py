import time
import math

from numpy import angle

from parser import Parser
from driveController import DriveController
# from camera import Camera
from cameraAIO import Camera

def wallDrive(dC: DriveController, dir, speedCurve, speedStraight, driveWall = False, angle = 45, dist = 310, skipTurn = False, skipWallDrive = False):    
    wall = dC.frontWall
    
    print(f"Wall drive with angle {angle}, distance {dist}, direction {dC.wallToString(dir)}, driveWall={driveWall}")
    
    if angle == 45:
        dist += 100
        if dir == dC.rightWall:
            wall = dC.angleRightWall
        else:
            wall = dC.angleLeftWall
            angle = -angle
        
    elif angle in (90, 0):
        if dir == dC.rightWall:
            wall = dC.frontWall
        else:
            wall = dC.frontWall
            angle = -angle

    if not skipTurn:
        dC.turn(speedCurve,angle)
    if not skipWallDrive:
        dC.driveToWall(speedStraight,angle,dist,wallDir=wall)
    dC.turn(speedCurve,0)
    if driveWall:
        dC.driveToWall(speedStraight,0,1000,wallDir=wall)



def unParkcounterClockwise(parser: Parser, dC: DriveController, cam: Camera):
    speedStraight=2
    speedCurve=1
    
    dC.customTurn(speedCurve, 180, 110)
    dC.turn(speedCurve, 0)
    dC.driveDist(speedStraight,0,200)
    dC.turn(speedCurve, -90)
    
def unParkAfterScan(parser: Parser, dC: DriveController, cam: Camera):
    speedStraight=2
    speedCurve=1
    
    dC.turn(speedCurve, 0)


def singleScanCounterClockwise(parser: Parser, dC: DriveController, cam: Camera):
    speedStraight=1

    
    # cam.loadImage("captureStore/3-0baseImage.jpg")
    # cam.pictureNum=2
    # cam.getObstacles2()
    # time.sleep(500)
    # return
    
    
    dC.tightTurn(0.75, -55)
    dC.brake()
    time.sleep(0.2)
    cam.captureImage()
    color1=cam.getObstacles1()
   
   
    dC.tightTurn(1, -90)
    dC.driveDist(speedStraight,-90,150)
    dC.brake()
    time.sleep(0.2)
    cam.captureImage()
    color2=cam.getObstacles2() 
    
    dC.tightTurn(-0.6, -150)
    dC.brake()
    time.sleep(0.2)
    cam.captureImage()
    color3=cam.getObstacles3() 
    color4=cam.getObstacles4() 
    
   
    
    print("Color 1:", parser.colorName(color1))     # section 1
    print("Color 2:", parser.colorName(color2))     # section 2
    print("Color 3:", parser.colorName(color3))     # section 3
    print("Color 4:", parser.colorName(color4))     # section 0
    
    return color1, color2, color3, color4

def singleScanClockwise(parser: Parser, dC: DriveController, cam: Camera):
    speedStraight=2
    speedCurve=1
    
    # cam.loadImage("captureStore/3-0baseImage.jpg")
    # cam.pictureNum=3
    # color2=cam.getObstacles2([230,390, 250,1000]) 
    # time.sleep(500)

    
    dC.tightTurn(0.6, -100)
    dC.brake()
    time.sleep(0.2)
    cam.captureImage()
    color1=cam.getObstacles1()
    color4=cam.getObstacles1b()
   
    dC.tightTurn(-0.5, -90)
    dC.brake()
    time.sleep(0.2)
    cam.captureImage()
    color2=cam.getObstacles2([230,390, 250,1000]) 
    
    
    dC.tightTurn(0.6, -30)
    dC.brake()
    time.sleep(0.2)
    cam.captureImage()
    color3=cam.getObstacles3b() 
    color4Left=cam.getObstacles4b()
    
    
   
    
    print("Color 1:", parser.colorName(color1))     # section 1
    print("Color 2:", parser.colorName(color2))     # section 2
    print("Color 3:", parser.colorName(color3))     # section 3
    print("Color 4:", parser.colorName(color4))     # section 0
    
    return color1, color2, color3, color4, color4Left


def obstacleChallengeSingle(parser: Parser, dC: DriveController, cam: Camera):
    distRight = 0
    distLeft = 0
    
    while (distLeft > 400 or distLeft == 0) and (distRight > 400 or distRight == 0):
        distRight = dC.getDist([3,4],3,dC.rightWall)
        distLeft = dC.getDist([3,4],3,dC.leftWall)
    
    print(f"Distance right: {distRight}, Distance left: {distLeft}")
    
    if distRight < 400:
        print("counterClockwise")
        counterClockwise(parser, dC, cam)
    else:
        print("Clockwise")
        clockwise(parser, dC, cam)
    

def parkCCW(parser: Parser, dC: DriveController):
    speedStraight=1
    speedCurve=1
    
    print("Parking")
    dC.driveToWall(speedStraight,0,1200)
    dC.brake()
    dC.driveAwayFromWall(-0.5, 0, 1150, dC.frontWall)
    dC.brake()
    time.sleep(3)
    dC.quickTurn(0.5,90)
    dC.driveToWall(0.5,90,70)
    
def parkCW(parser: Parser, dC: DriveController):
    speedStraight=1
    speedCurve=1
    
    print("Parking")
    dC.turn(speedCurve,0)
    dC.driveAwayFromWall(0.5, 0, 1050)
    dC.brake()
    dC.quickTurn(0.5,90)
    dC.brake()
    time.sleep(3)
    dC.driveToWall(0.5,90,70)
    
    
    
   
def counterClockwise(parser: Parser, dC: DriveController, cam: Camera):
    speedStraight=2
    speedCurve=1
    speedCurveSlow=0.65
    parser.Direction = parser.CCW
    
    parser.assignAllObstacles(singleScanCounterClockwise(parser, dC, cam))
    # parser.assignAllObstaclesCustom(Parser.GREEN, Parser.GREEN, Parser.GREEN, Parser.RED)
      
    unParkAfterScan(parser, dC, cam)
    
    dC.section += 1
    for j in range(3):
        for i in range(4):
            if i == 3:
                wallDriveDist = 600
            else:
                wallDriveDist = 450
                
            print("Obstacle:", parser.colorName(parser.checkSection(dC.section)))

            if parser.checkSection(dC.section) == parser.GREEN:                # obstacles green:
                dC.turn(speedCurve,0)
                dC.driveAwayFromWall(speedStraight, 0, 1000)
                dC.driveDist(speedStraight,0,500)

            elif parser.checkSection(dC.section) in (parser.RED, None):          # obstacles red or unknown
                print(f"Color thingy: {parser.colorName(parser.checkSection(dC.prevSection()))}")
                dC.driveToWall(speedStraight,90,wallDriveDist)
                dC.turn(speedCurve,0)
                dC.driveDist(speedStraight,0,500)
            
            if i == 3 and j == 2:
                parkCCW(parser, dC)
            else:
                dC.driveToWall(speedStraight,0,1050, 600)
            
            dC.section = dC.nextSection()
            
            if dC.end():
                print("\n--------------------- END --------------------\n")
                return
            
            print("!!!!!!!!!!!!!!!!!!!!! DONE !!!!!!!!!!!!!!!!!!!!")
        parser.round += 1
        print("********************* Super DONE ********************")
    
    parser.endTime = time.time()
    dC.brake()


def clockwise(parser: Parser, dC: DriveController, cam: Camera):
    speedStraight=2
    speedCurve=1
    speedCurveSlow=0.65
    parser.Direction = parser.CW

    parser.assignAllObstacles(singleScanClockwise(parser, dC, cam))
    # parser.assignAllObstaclesCustom(Parser.GREEN, Parser.RED, Parser.GREEN, Parser.RED)
            
    unParkAfterScan(parser, dC, cam)
    
    if parser.obstacles[2] == parser.GREEN:
        dC.turn(speedCurve,45)
        dC.driveDist(speedStraight,45,100)
        dC.turn(speedCurve,0)
        dC.driveToWall(speedStraight,0,1000)
    elif parser.obstacles[2] == parser.RED:
        dC.turn(speedCurve,-60)
        dC.turn(speedCurve,0)
        dC.driveToWall(speedStraight,0,1000)
    else:
        dC.driveToWall(speedStraight,0,1000)
        
    
    dC.section += 1
    for j in range(3):
        for i in range(4):
            if i == 3:
                wallDriveDist = 600
            else:
                wallDriveDist = 400
                
            print("Obstacle:", parser.colorName(parser.checkSection(dC.section, True)))

            if not (i == 3 and j == 2):
                if parser.checkSection(dC.section, True) == parser.RED:                # obstacles red:
                    dC.turn(speedCurve,0)
                    dC.driveAwayFromWall(speedStraight, 0, 1000)				
                    dC.driveDist(speedStraight,0,500)

                elif parser.checkSection(dC.section, True) in (parser.GREEN, None):          # obstacles green or unknown
                    print(f"Color thingy: {parser.colorName(parser.checkSection(dC.prevSection()))}")
                    dC.driveToWall(speedStraight,90,wallDriveDist)
                    dC.turn(speedCurve,0)
                
                dC.driveToWall(speedStraight,0,1100)
                
                dC.section = dC.nextSection()
            else:
                if parser.obstacles[0] == parser.GREEN:
                    dC.driveToWall(speedStraight,90,wallDriveDist)
                parkCW(parser, dC)
                
            
            if dC.end():
                print("\n--------------------- END --------------------\n")
                return
            
            print("!!!!!!!!!!!!!!!!!!!!! DONE !!!!!!!!!!!!!!!!!!!!")
        parser.round += 1
        print("********************* Super DONE ********************")
    
    parser.endTime = time.time()
    dC.brake()
