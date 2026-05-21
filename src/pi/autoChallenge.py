import time
import math
import obstacleChallengeSingle
import openChallenge

from numpy import angle

from parser import Parser
from driveController import DriveController
# from camera import Camera
from cameraAIO import Camera

def autoChallenge(parser: Parser, dC: DriveController, cam: Camera):
    for _ in range(100):
        frontDist = dC.getDist([3,4],3,dC.frontWall)
        if frontDist > 0:
            break
    
    if frontDist < 300 and frontDist > 0:
        obstacleChallengeSingle.obstacleChallengeSingle(parser, dC, cam)
    else:
        openChallenge.openChallenge(parser, dC)