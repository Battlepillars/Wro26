import time
import math

from numpy import angle

from parser import Parser
from driveController import DriveController
# from camera import Camera
from cameraAIO import Camera

def wallDrive(dC: DriveController, dir, speedCurve, speedStraight, driveWall = False, angle = 45, dist = 310, skipTurn = False):    
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
    dC.driveToWall(speedStraight,angle,dist,wall)
    dC.turn(speedCurve,0)
    if driveWall:
        dC.driveToWall(speedStraight,0,1000,wall)



def unParkClockWise(parser: Parser, dC: DriveController, cam: Camera):
    speedStraight=2
    speedCurve=1
    
    dC.customTurn(speedCurve, 180, 110)
    dC.turn(speedCurve, 0)
    dC.driveDist(speedStraight,0,200)
    dC.turn(speedCurve, -90)
    
def unParkClockWiseAfterScan(parser: Parser, dC: DriveController, cam: Camera):
    speedStraight=2
    speedCurve=1
    
    dC.turn(speedCurve, 0)

def singleScan(parser: Parser, dC: DriveController, cam: Camera):
    speedStraight=2
    speedCurve=1
    
    # cam.loadImage("capture/2-0baseImage.jpg")
    # cam.pictureNum=2
    # cam.getObstacles2()
    # return
    
    dC.customTurn(speedCurve, 180, 110)
    dC.brake()
    # time.sleep(2)
    cam.captureImage()
    color1=cam.getObstacles1()

    dC.customTurn(speedCurve, 180, 70)
    dC.brake()
    # time.sleep(2)
    cam.captureImage()
    color2=cam.getObstacles2()

    dC.customTurn(speedCurve, 0,-100)
    dC.brake()
    # time.sleep(2)
    cam.captureImage()
    color3=cam.getObstacles3()
    color4=cam.getObstacles4()
    
    print("Color 1:", parser.colorName(color1))     # section 1
    print("Color 2:", parser.colorName(color2))     # section 2
    print("Color 3:", parser.colorName(color3))     # section 3
    print("Color 4:", parser.colorName(color4))     # section 0
    
    return color1, color2, color3, color4


def clockwise(parser: Parser, dC: DriveController, cam: Camera):
    speedStraight=2
    speedCurve=1
    speedCurveSlow=0.65
    
    color1, color2, color3, color4 = singleScan(parser, dC, cam)
    # parser.assignMultibelObstacles(0, color4)
    # parser.assignMultibelObstacles(1, color1)
    # parser.assignMultibelObstacles(2, color2)
    # parser.assignMultibelObstacles(3, color3)
    parser.assignMultibelObstacles(0, parser.RED)
    parser.assignMultibelObstacles(1, parser.RED)
    parser.assignMultibelObstacles(2, parser.GREEN)
    parser.assignMultibelObstacles(3, parser.GREEN)
    
            
    unParkClockWiseAfterScan(parser, dC, cam)
    dC.section += 1
    for j in range(3):
        for i in range(4):
            if i == 3:
                wallDriveDist = 600
            else:
                wallDriveDist = 400
                
            print("Obstacle:", parser.colorName(parser.checkSection(dC.section)))

            if parser.checkSection(dC.section) == parser.GREEN:                # obstacles green:
                dC.turn(speedCurve,0)
                dC.driveAwayFromWall(speedStraight, 0, 150)
                distRight = dC.getDist([0,1,2,3,4,5,6,7],3,dC.rightWall)
                print("distright green: "+str(distRight))
                if distRight <= 620:
                    if distRight <= 700:
                        # driveDist = 230-(distRight-400)*math.sqrt(2)
                        driveDist = 0
                        print("Calculated drive distance:", driveDist)
                        if driveDist > 0:
                            dC.turn(speedCurveSlow,-45)
                        else:
                            dC.quickTurn(speedCurveSlow,-45)
                        dC.driveDist(speedStraight,-45,driveDist)
                        dC.turn(speedCurve,0)
                    else:
                        print("\n\n\nToo far from wall, skipping wall drive.\n\n\n")
                dC.driveAwayFromWall(speedStraight, 0, 1000)				
                dC.driveDist(speedStraight,0,500)

            elif parser.checkSection(dC.section) in (parser.RED, None):          # obstacles red or unknown
                print(f"Color thingy: {parser.colorName(parser.checkSection(dC.prevSection()))}")
                dC.driveToWall(speedStraight,90,wallDriveDist)
                dC.turn(speedCurve,0)
            
            dC.driveToWall(speedStraight,0,1000)
            
            dC.section = dC.nextSection()
            
            if dC.end():
                print("\n--------------------- END --------------------\n")
                return
            
            print("!!!!!!!!!!!!!!!!!!!!! DONE !!!!!!!!!!!!!!!!!!!!")
        print("********************* Super DONE ********************")
    
    parser.endTime = time.time()
    dC.brake()
