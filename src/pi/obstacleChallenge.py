import time
import math

from parser import Parser
from driveController import DriveController
from camera import Camera


def clockwise(parser: Parser, dC: DriveController, cam: Camera):
    parser.obstacles[0] = cam.captureImage()
    
    if parser.obstacles[0] == parser.GREEN or parser.obstacles[0] == None:
        dC.driveAwayFromWall(2, 0, 350)
        distRight = dC.getDist([0,1,2,3,4,5,6,7],3,dC.rightWall)
        print(distRight)
        dC.turn(2,-45)
        dC.driveDist(2,-45,230-(distRight-500)*math.sqrt(2))
        dC.turn(2,0)
        dC.driveAwayFromWall(2, 0, 800)
        # parser.obstacles[1] = cam.captureImage()
        if parser.obstacles[1] == parser.RED or True:
            dC.turn(2,90)
            dC.driveToWall(2, 90, 200, dC.frontWall)
            dC.turn(2,0)
            dC.driveDist(2,0,1500)
            dC.brake()
        else:
            dC.driveDist(2,0,2000)
            dC.brake()
    if parser.obstacles[0] == parser.RED:
        dC.turn(2,45)
        dC.driveToWall(2, 45, 200)
        dC.turn(2,0)
        dC.driveAwayFromWall(2, 0, 800)
        parser.obstacles[1] = cam.captureImage()
        if parser.obstacles[0] == parser.RED:
            pass
        dC.driveDist(2,0,2000)
        dC.brake()