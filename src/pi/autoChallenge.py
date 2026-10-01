import obstacleChallenge
import openChallenge

from parser import Parser
from driveController import DriveController
from cameraTower import Camera

def autoChallenge(parser: Parser, dC: DriveController, cam: Camera):
    """@brief Auto-select the open or obstacle challenge from the start position.

    Reads the front ToF distance a few times to get a valid sample: a wall
    close in front means the car is parked for the obstacle challenge,
    otherwise it runs the open challenge.
    @param parser Parser instance with shared sensor state.
    @param dC     DriveController providing motion primitives.
    @param cam    Camera used by the obstacle challenge.
    @return None
    """
    for _ in range(100):
        frontDist = dC.getDist([3,4],3,dC.frontWall)
        if frontDist > 0:   # wait for a valid (non-zero) distance reading
            break
    
    if frontDist < 300 and frontDist > 0:   # close wall ahead -> obstacle challenge
        obstacleChallenge.obstacleChallenge(parser, dC, cam)
    else:
        openChallenge.openChallenge(parser, dC)