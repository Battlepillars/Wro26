from parser import Parser
from driveController import DriveController

def clockwise(Parser: Parser, dC: DriveController):
    turnSpeed=2
    speed=2
    for i in range(3):
        dC.driveAlongWall(speed,0,dC.leftWall)
        dC.turn(turnSpeed,-90)
        dC.driveDist(speed,-90,750)
        dC.driveAlongWall(speed,-90,dC.leftWall)
        dC.turn(turnSpeed,-180)
        dC.driveDist(speed,-180,750)
        dC.driveAlongWall(speed,-180,dC.leftWall)
        dC.turn(turnSpeed,90)
        dC.driveDist(speed,90,750)
        dC.driveAlongWall(speed,90,dC.leftWall)
        dC.turn(turnSpeed,0)
        dC.driveDist(speed,0,750)

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