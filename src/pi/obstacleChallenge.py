import time
import math

from parser import Parser
from driveController import DriveController
from camera import Camera

def wallDrive(dC: DriveController, dir, speedCurve, speedStraight, driveWall = False, angle = 45):
    dist = 310

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
    if driveWall:
        dC.driveToWall(speedStraight,0,1000,wall)



def clockwise(parser: Parser, dC: DriveController, cam: Camera):
    speedStraight=2
    speedCurve=1
    skipScan = False
    for i in range(4):
        dC.driveAwayFromWall(speedStraight, 0, 150)
        distRight = dC.getDist([0,1,2,3,4,5,6,7],3,dC.rightWall,dC.smallest)
        if distRight <= 0:
            distRight = 800
        print("distright: "+str(distRight))
        backDist = dC.getDist([0,1,2,3,4,5,6,7],3,dC.backWall)
        print("Back dist:",backDist)
        if skipScan == False:
            if backDist < 100:
                parser.obstacles[0+dC.section*3] = cam.captureImage(leftDist = distRight/1.2)
            else:
                parser.obstacles[0+dC.section*3] = cam.captureImage(leftDist = distRight/1.2, upDist = backDist/3)
        elif skipScan:
            skipScan = False
        print("Obstacle detected:", parser.obstacles[0+dC.section*3])

        if parser.obstacles[0+dC.section*3] == parser.GREEN:                #first row of obstacles green
            print(skipScan)
            if skipScan != parser.GREEN:
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
            else:
                skipScan = False
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
                skipScan = True
                dC.driveDist(speedStraight,0,500)
            elif parser.obstacles[2+dC.section*3] == parser.RED:
                wallDrive(dC, dC.rightWall, speedCurve, speedStraight, True, 90)
            elif parser.obstacles[2+dC.section*3] == None:
                skipScan = True
                dC.driveDist(speedStraight,0,500)

        elif parser.obstacles[0+dC.section*3] == parser.RED:          #first row of obstacles red
            if skipScan != parser.RED:
                dC.driveAwayFromWall(speedStraight, 0, 150)
                if distRight >= 250:
                    wallDrive(dC, dC.rightWall, speedCurve, speedStraight, False)
            else: 
                skipScan = False
            dC.driveAwayFromWall(speedStraight, 0, 1000)
            # parser.obstacles[1+dC.section*3] = cam.captureImage()
            # if parser.obstacles[1+dC.section*3] == parser.RED:     # sharp turn
            #     pass
            dC.driveDist(speedStraight,0,700)
            parser.obstacles[2+dC.section*3] = cam.captureImage(upDist=35)
            if parser.obstacles[2+dC.section*3] == parser.GREEN:                # third row green
                skipScan = True
                wallDrive(dC, dC.leftWall, speedCurve, speedStraight, True, 90)
            elif parser.obstacles[2+dC.section*3] == parser.RED or parser.obstacles[2+dC.section*3] == None:    # third row red or nothing
                pass # dC.driveToWall(speedStraight,0,1000,dC.frontWall)
        
        elif parser.obstacles[0+dC.section*3] == None:              # second row of obstacles
            dC.driveAwayFromWall(speedStraight,0,700)
            parser.obstacles[1+dC.section*3] = cam.captureImage()
            if parser.obstacles[1+dC.section*3] == parser.GREEN:
                skipScan = True
                if distRight >= 800:
                    dC.driveDist(speedStraight,0,500)
                elif distRight >= 600:
                    wallDrive(dC, dC.leftWall, speedCurve, speedStraight, True, 45)
                elif distRight <= 600:
                    wallDrive(dC, dC.leftWall, speedCurve, speedStraight, True, 90)    

            elif parser.obstacles[1+dC.section*3] == parser.RED:
                if distRight >= 600:
                    wallDrive(dC, dC.rightWall, speedCurve, speedStraight, True, 90)
                elif distRight >= 250:
                    wallDrive(dC, dC.rightWall, speedCurve, speedStraight, True)
                else:
                    dC.driveDist(speedStraight,0,500)
                
            elif parser.obstacles[1+dC.section*3] == None:
                dC.driveDist(speedStraight,0,500)
                parser.obstacles[2+dC.section*3] = cam.captureImage()
                if parser.obstacles[2+dC.section*3] == parser.GREEN:
                    skipScan = True
                    if distRight <= 700:
                        wallDrive(dC, dC.leftWall, speedCurve, speedStraight, True)
                    else:
                        dC.driveDist(speedStraight,0,200)
                
                elif parser.obstacles[2+dC.section*3] == parser.RED:
                    if distRight >= 250:
                        wallDrive(dC, dC.rightWall, speedCurve, speedStraight, True)
                    else:
                        dC.driveDist(speedStraight,0,200)
            
        if skipScan:
            dC.driveToWall(speedStraight,0,1200,dC.frontWall)
        else:
            dC.driveToWall(speedStraight,0,1000,dC.frontWall)
        
        if skipScan and i != 3:
            parser.obstacles[0+(dC.section+1)*3] = cam.captureImage()
            if parser.obstacles[0+(dC.section+1)*3] == parser.GREEN:
                skipScan = parser.GREEN
            elif parser.obstacles[0+(dC.section+1)*3] == parser.RED:
                skipScan = parser.RED
                dC.driveToWall(speedStraight,0,400)
        
        dC.turn(speedCurve,-90)
        dC.section += 1
        print("\n\n!!!!!!!!!!!!!!!!!!!!! DONE !!!!!!!!!!!!!!!!!!!! \n\n")
    
    dC.brake()
