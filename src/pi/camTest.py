import time
import math

from parser import Parser
from driveController import DriveController
from camera import Camera


def test(parser: Parser, dC: DriveController, cam: Camera):
    parser.debugCam = True
    while True:
        distRight = dC.getDist([0,1,2,3,4,5,6,7],3,dC.rightWall,dC.smallest)
        backDist = dC.getDist([0,1,2,3,4,5,6,7],3,dC.backWall)
        parser.obstacles[0+dC.section*3] = cam.captureImage(leftDist = 300)


