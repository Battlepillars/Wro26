import time

from parser import Parser
from driveController import DriveController


#
def openChallenge(parser: Parser, dC: DriveController):
    """
    @brief Execute the WRO open challenge routine.
    
    @param parser  Parser instance that holds shared sensor data and round state.
    @param dC      DriveController used for all motion primitives.
    """
    turnSpeed = 1.3   # speed for curves
    speed     = 2     # speed for drive straight

    for i in range(3):   # three laps around the track
        # --- Section 1: heading 0° ---
        if i == 0:
            # First lap only: detect CW or CCW direction
            # drive forward until a wall disappears and remeber direction (CW or CCW)
            wall = dC.findeDirection(speed, 0)   
            print("Wall:", wall)    
        else:
            dC.driveAlongWall(speed, 0, wall)  # drive forward until a wall disappears
        
        # --- Section 1: heading -90° ---
        dC.turn(turnSpeed, -90)               # turn to -90°
        dC.driveDist(speed, -90, 750)         # drive 750 mm
        dC.driveAlongWall(speed, -90, wall)   # drive forward until a wall disappears
        
        # --- Section 2: heading -180° ---
        dC.turn(turnSpeed, -180)              # turn to -180°
        dC.driveDist(speed, -180, 750)        # drive 750 mm
        dC.driveAlongWall(speed, -180, wall)  # drive forward until a wall disappears
        
        # --- Section 3: heading +90° ---
        dC.turn(turnSpeed, 90)                # turn to +90°
        dC.driveDist(speed, 90, 750)          # drive 750 mm
        dC.driveAlongWall(speed, 90, wall)    # drive forward until a wall disappears
        
        # --- Section 0: heading 0° (back to start heading) ---
        dC.turn(turnSpeed, 0)                 # turn back to 0°
        
        if i == 2:
            # Final lap: drive away from the back wall to reach the parking zone.
            dC.driveAwayFromWall(speed, 0, 1100)
        else:
            # Not the final lap: drive 750 mm
            dC.driveDist(speed, 0, 750)
        
        parser.round += 1   # increment the completed-round counter
    
    parser.endTime = time.time()   # record finish timestamp
    dC.brake()                     # bring the robot to a full stop


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