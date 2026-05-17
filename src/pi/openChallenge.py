import time

from parser import Parser
from driveController import DriveController


def openChallenge(parser: Parser, dC: DriveController):
    turnSpeed=1.3
    speed=2
    for i in range(3):
        if i == 0:
            wall = dC.findeDirection(speed,0)
            print("Wall:", wall)
        else:
            dC.driveAlongWall(speed,0,wall)
        dC.turn(turnSpeed,-90)
        dC.driveDist(speed,-90,750)
        dC.driveAlongWall(speed,-90,wall)
        dC.turn(turnSpeed,-180)
        dC.driveDist(speed,-180,750)
        dC.driveAlongWall(speed,-180,wall)
        dC.turn(turnSpeed,90)
        dC.driveDist(speed,90,750)
        dC.driveAlongWall(speed,90,wall)
        dC.turn(turnSpeed,0)
        if i == 2:
            dC.driveAwayFromWall(speed, 0, 1100)
        else:
            dC.driveDist(speed,0,750)
        parser.round += 1
    parser.endTime = time.time()
    dC.brake()
    


# def clockwise(parser: Parser, dC: DriveController):
#     speed = 3
#     for i in range(3):
#         dist = 1600
#         dist2 = 0
#         dC.driveAlongWall(speed, 0, dC.rightWall)
#         dC.driveDist(speed,0,dist2)
#         dC.driveDist(speed,90,dist)
#         dC.driveAlongWall(speed, 90, dC.rightWall)
#         dC.driveDist(speed,90,dist2)
#         dC.driveDist(speed,180,dist)
#         dC.driveAlongWall(speed, 180, dC.rightWall)
#         dC.driveDist(speed,180,dist2)
#         dC.driveDist(speed,-90,dist)
#         dC.driveAlongWall(speed, -90, dC.rightWall)
#         if i < 2:
#             dC.driveDist(speed,-90,dist2)
#             dC.driveDist(speed,0,dist)
#         else:
#             dC.driveDist(speed,0,300)
#     dC.brake()
    

# def clockwise(parser: Parser, dC: DriveController):
#     speed = 2
#     for i in range(3):
#         dist = 1500
#         dist2 = 1500
#         dC.driveAwayFromWall(speed,0)
#         dC.driveDist(speed,0,dist2)
#         dC.driveDist(speed,90,dist)
#         dC.driveAwayFromWall(speed, 90)
#         dC.driveDist(speed,90,dist2)
#         dC.driveDist(speed,180,dist)
#         dC.driveAwayFromWall(speed, 180)
#         dC.driveDist(speed,180,dist2)
#         dC.driveDist(speed,-90,dist)
#         dC.driveAwayFromWall(speed, -90)
#         if i < 2:
#             dC.driveDist(speed,-90,dist2)
#             dC.driveDist(speed,0,dist)
#         else:
#             dC.driveDist(speed,0,300)
#     dC.brake()