import time
import math

from parser import Parser
from driveController import DriveController
from camera import Camera

def wallDrive(dC: DriveController, dir, speedCurve, speedStraight, driveWall = False, angle = 45):
    wall = dC.backWall
    if dir == dC.rightWall:
        dC.turn(speedCurve,angle)
        dC.driveToWall(speedStraight,angle,310,wall)
        dC.turn(speedCurve,0)
        if driveWall:
            dC.driveToWall(speedStraight,0,1000,wall)
    else:
        dC.turn(speedCurve,-angle)
        dC.driveToWall(speedStraight,-angle,310,wall)
        dC.turn(speedCurve,0)
        if driveWall:
            dC.driveToWall(speedStraight,0,1000,wall)



def clockwise(parser: Parser, dC: DriveController, cam: Camera):
    speedStraight=2
    speedCurve=1
    for i in range(4):
        distRight = dC.getDist([0,1,2,3,4,5,6,7],3,dC.rightWall)
        if distRight <= 0:
            distRight = 1000
        print("distright: "+str(distRight))
        backDist = dC.getDist([0,1,2,3,4,5,6,7],3,dC.backWall)
        print("Back dist:",backDist)
        if backDist < 100:
            parser.obstacles[0+dC.section*3] = cam.captureImage(leftDist = distRight/1.2)
        else:
            parser.obstacles[0+dC.section*3] = cam.captureImage(leftDist = distRight/1.2, upDist = backDist/2.3)
        
        
        if parser.obstacles[0+dC.section*3] == parser.GREEN:                #first row of obstacles green
            dC.driveAwayFromWall(speedStraight, 0, 150)
            distRight = dC.getDist([0,1,2,3,4,5,6,7],3,dC.rightWall)
            print("distright: "+str(distRight))
            if distRight <= 700:
                dC.turn(speedCurve,-45)
                dC.driveDist(speedStraight,-45,230-(distRight-500)*math.sqrt(2))
                dC.turn(speedCurve,0)
            dC.driveAwayFromWall(speedStraight, 0, 1000)
            # parser.obstacles[1+dC.section*3] = cam.captureImage()
            # if parser.obstacles[1+dC.section*3] == parser.RED:					# sharp turn
            # 	dC.turn(speedCurve,90)
            # 	dC.driveToWall(speedStraight, 90, 300, dC.frontWall)
            # 	dC.turn(speedCurve,0)
            # 	dC.driveDist(speedStraight,0,1000)
            # 	dC.brake()
            # else:												
            dC.driveDist(speedStraight,0,300)
            parser.obstacles[2+dC.section*3] = cam.captureImage()
            if parser.obstacles[2+dC.section*3] == parser.GREEN:
                dC.driveDist(speedStraight,0,500)
            elif parser.obstacles[2+dC.section*3] == parser.RED:
                wallDrive(dC, dC.rightWall, speedCurve, speedStraight, True)
            elif parser.obstacles[2+dC.section*3] == None:
                dC.driveDist(speedStraight,0,500)

        elif parser.obstacles[0+dC.section*3] == parser.RED:          #first row of obstacles red
            dC.driveAwayFromWall(speedStraight, 0, 150)
            if distRight >= 250:
                wallDrive(dC, dC.rightWall, speedCurve, speedStraight, False)
            dC.driveAwayFromWall(speedStraight, 0, 1000)
            # parser.obstacles[1+dC.section*3] = cam.captureImage()
            # if parser.obstacles[1+dC.section*3] == parser.RED:     # sharp turn
            #     pass
            dC.driveDist(speedStraight,0,700)
            parser.obstacles[2+dC.section*3] = cam.captureImage(upDist=35)
            if parser.obstacles[2+dC.section*3] == parser.GREEN:                # third row green
                wallDrive(dC, dC.leftWall, speedCurve, speedStraight, True, 90)
            elif parser.obstacles[2+dC.section*3] == parser.RED or parser.obstacles[2+dC.section*3] == None:    # third row red or nothing
                dC.driveToWall(speedStraight,0,1000,dC.frontWall)
        
        elif parser.obstacles[0+dC.section*3] == None:              # second row of obstacles
            dC.driveAwayFromWall(speedStraight,0,700)
            parser.obstacles[1+dC.section*3] = cam.captureImage()
            if parser.obstacles[1+dC.section*3] == parser.GREEN:
                if distRight <= 700:
                    wallDrive(dC, dC.leftWall, speedCurve, speedStraight, True)
                else:
                    dC.driveDist(speedStraight,0,200)
            elif parser.obstacles[1+dC.section*3] == parser.RED:
                if distRight >= 250:
                    wallDrive(dC, dC.rightWall, speedCurve, speedStraight, True)
                else:
                    dC.driveDist(speedStraight,0,200)
                dC.driveDist(speedStraight,0,500)
            elif parser.obstacles[1+dC.section*3] == None:
                dC.driveDist(speedStraight,0,500)
                parser.obstacles[2+dC.section*3] = cam.captureImage()
                if parser.obstacles[2+dC.section*3] == parser.GREEN:
                    if distRight <= 700:
                        wallDrive(dC, dC.leftWall, speedCurve, speedStraight, True)
                    else:
                        dC.driveDist(speedStraight,0,200)
                elif parser.obstacles[2+dC.section*3] == parser.RED:
                    if distRight >= 250:
                        wallDrive(dC, dC.rightWall, speedCurve, speedStraight, True)
                    else:
                        dC.driveDist(speedStraight,0,200)
                    dC.driveDist(speedStraight,0,500)
        dC.turn(speedCurve,-90)
        dC.section += 1
        print("\n\n!!!!!!!!!!!!!!!!!!!!! DONE !!!!!!!!!!!!!!!!!!!! \n\n")
    
    dC.brake()
