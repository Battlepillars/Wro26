import time
import math

from parser import Parser
from driveController import DriveController
from camera import Camera

def wallDrive(dC: DriveController, dir, speedCurve, speedStraight, driveWall = False, angle = 45):
    dist = 310
    wall = dC.frontWall
    
    if angle == 45:
        dist += 100
        if dir == dC.rightWall:
            wall = dC.angleRightWall
        else:
            wall = dC.angleLeftWall
            angle = -angle
        
    elif angle == 90:
        if dir == dC.rightWall:
            wall = dC.frontWall
        else:
            wall = dC.frontWall
            angle = -angle

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




def clockwise(parser: Parser, dC: DriveController, cam: Camera):
    speedStraight=2
    speedCurve=1
    skipScan = False
    
    scanUpDist = -50
    
    unParkClockWise(parser, dC, cam)
    dC.section += 1
    
    for i in range(4):
        dC.driveAwayFromWall(speedStraight, 0, 150)
        distRight = dC.getDist([1,2,3,4,5,6],3,dC.rightWall,dC.smallest)
        if distRight <= 0:
            distRight = 800
        print("distright: "+str(distRight))
        backDist = dC.getDist([0,1,2,3,4,5,6,7],4,dC.backWall)
        print("Back dist:",backDist)
        if not skipScan == parser.RED:
            val = cam.captureImage(leftDist = distRight/1.5, upDist = scanUpDist )
            if val is not None:
                parser.assignMultibelObstacles(dC.section, val)
        print("Obstacle detected:", parser.obstacles[0+dC.section*3])

        if parser.checkSection(dC.section) == parser.GREEN:                #obstacles green:
            dC.driveAwayFromWall(speedStraight, 0, 150)
            distRight = dC.getDist([0,1,2,3,4,5,6,7],3,dC.rightWall)
            print("distright: "+str(distRight))
            if distRight <= 700:
                driveDist = 230-(distRight-400)*math.sqrt(2)
                print("Calculated drive distance:", driveDist)
                if driveDist > 0:
                    dC.turn(speedCurve,-45)
                else:
                    dC.quickTurn(speedCurve,-45)
                dC.driveDist(speedStraight,-45,driveDist)
                dC.turn(speedCurve,0)
            else:
                print("\n\n\nToo far from wall, skipping wall drive.\n\n\n")
            dC.driveAwayFromWall(speedStraight, 0, 1000)				
            dC.driveDist(speedStraight,0,500)
            skipScan = True

        elif parser.checkSection(dC.section) == parser.RED:          #first row of obstacles red
            if skipScan == parser.RED:
                wallDrive(dC, dC.rightWall, speedCurve, speedStraight, True, 90)
                skipScan = False
            else:
                dC.driveAwayFromWall(speedStraight, 0, 150)
                print("Dist right red: "+str(distRight))
                if distRight >= 250:
                    print("Wall drive")
                    wallDrive(dC, dC.rightWall, speedCurve, speedStraight)
                dC.driveAwayFromWall(speedStraight, 0, 1000)
                dC.driveDist(speedStraight,0,700)
        
        if skipScan:
            dC.driveToWall(speedStraight,0,1200,dC.frontWall)
        else:
            dC.driveToWall(speedStraight,0,1000,dC.frontWall)
        
        if skipScan and i != 3:
            print("Section:", dC.section)
            parser.assignMultibelObstacles(dC.nextSection(), cam.captureImage(rightDist=300))
            if parser.checkSection(dC.nextSection()) == parser.RED:
                dC.driveToWall(speedStraight,0,400)
            else:
                dC.driveToWall(speedStraight,0,1100)
                dC.turn(speedCurve,-55)
                parser.assignMultibelObstacles(dC.nextSection(), cam.captureImage())
                if parser.checkSection(dC.nextSection()) == None:
                    skipScan = False
                elif parser.checkSection(dC.nextSection()) == parser.RED:
                    skipScan = parser.RED
        
        if skipScan == parser.RED:
            dC.turn(speedCurve,0)
        else:
            dC.turn(speedCurve,-90)
        dC.section = dC.nextSection()
        
        print("\n\n!!!!!!!!!!!!!!!!!!!!! DONE !!!!!!!!!!!!!!!!!!!!\n\n")
    
    dC.brake()
