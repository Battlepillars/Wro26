import time
from subprocess import call

from parser import Parser
from driveController import DriveController
from cameraTower import Camera

def wallDrive(parser: Parser, dC: DriveController, dir, speedCurve, speedStraight, angle = 45, i = 0):
    """@brief Change lane across the course by steering out and back to a wall.

    Turns to the given angle, drives toward the chosen (angled or side) wall,
    straightens out, then follows the far wall – optionally running a recovery
    move if it overshoots past the next obstacle.
    @param parser        Parser with obstacle and direction state.
    @param dC            DriveController providing motion primitives.
    @param dir           target wall to end up following.
    @param speedCurve    float speed used during the turns.
    @param speedStraight float speed used on the straight segments.
    @param angle         int lane-change angle (45 or 90 degrees).
    @param i             int section counter (lengthens the last section).
    @return None
    """
    if i == 3:
        dist = 600       # last section of the lap is longer
    else:
        dist = 350
    
    
    # Pick the sensor that faces the wall for this heading and negate the angle
    # when heading toward the left wall.
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
    # dC.driveToWall(speedStraight,0,1000,wall)
    
    print("Dir: " + str(dir))
    if dir == dC.leftWall:
        print("Dir: " + str(dC.convertDir(parser, dC.leftWall)))
        wallLost = dC.driveToWall(speedStraight,0,1000,900,avoidWall=dC.convertDir(parser, dC.leftWall))    # dist = 1000, min = 900
        # drove to far (past the next obstacle):
        if wallLost and parser.checkSectionAuto(dC.nextSection()) == parser.GREEN:
            dC.brake()
            # dC.driveAwayFromWall(-0.5,0,900,dC.frontWall)
            dC.driveDist(-0.5,0,600)
            print("Dir: " + str(dir))
            dC.driveToWall(-0.5,0,300,wallDir=dC.convertDir(parser, dC.leftWall))
            dC.brake()
            dC.driveToWall(0.5,0,300,wallDir=dC.convertDir(parser, dC.leftWall))
            dC.driveDist(0.5,0,200)
            dC.brake()
    else:
        dC.driveToWall(speedStraight,0,1000, 900, avoidWall=None)
    
def unParkCW(parser: Parser, dC: DriveController):
    """@brief Leave the start/parking zone when running clockwise.

    Picks the exit maneuver based on the first obstacle's color in the
    current section.
    @param parser Parser with the scanned obstacle layout.
    @param dC     DriveController providing motion primitives.
    @return None
    """
    speedStraight=1
    speedCurve=1
    speedCurveSlow=0.6
    sectionObstacleList = parser.checkSectionMulti(dC.section, True)
    print("First obstacle: " + str(sectionObstacleList[0]) + ", second obsacle: " + str(sectionObstacleList[1]))
    if sectionObstacleList[0] == parser.GREEN:
        dC.tightTurn(speedCurveSlow, -40)
        dC.driveDist(speedStraight, -40, 200)
        dC.turn(speedCurve, 0)
        dC.driveToWall(speedStraight,0,1050, 900, minTravel=500)
    else:
        dC.tightTurn(speedCurveSlow, -90)
        # dC.driveDist(speedStraight, -40, 200)
        dC.driveToWall(speedStraight,-90,300, 0)
        dC.turn(speedCurve, 0)
        dC.driveToWall(speedStraight,0,1050, 900)

def unParkCCW(parser: Parser, dC: DriveController):
    """@brief Leave the start/parking zone when running counter-clockwise.

    @param parser Parser with the scanned obstacle layout.
    @param dC     DriveController providing motion primitives.
    @return None
    """
    speedStraight=1
    speedStraightSlow=0.6
    speedCurve=1
    speedCurveSlow=0.6
    
    sectionObstacleList = parser.checkSectionMulti(dC.section)
    print("First obstacle: " + str(sectionObstacleList[0]) + ", second obsacle: " + str(sectionObstacleList[1]))
    if parser.obstacles[2] == parser.GREEN:
        dC.tightTurn(speedCurveSlow, -90)
        dC.driveToWall(speedStraightSlow,-90,300, 0)
        dC.brake()
        dC.tightTurn(speedCurveSlow, 0)
    else:
        dC.tightTurn(speedCurveSlow, -40)
        dC.driveDist(speedStraight, -40, 350)

def parkCW(parser: Parser, dC: DriveController):
    """@brief Perform the final parallel-parking maneuver for a clockwise run.

    Chooses the approach depending on the parking-zone obstacle color and
    backs into the magenta parking bay.
    @param parser Parser with the scanned obstacle layout.
    @param dC     DriveController providing motion primitives.
    @return None
    """
    speedStraight=1
    speedStraightSlow=0.6
    speedStraightVerySlow=0.3
    speedCurve=1
    speedCurveSlow=0.6
    
    sectionObstacleList = parser.checkSectionMulti(dC.section, True)
    prevSectionObstacleList = parser.checkSectionMulti(dC.prevSection(), True)
    
    print("First obstacle: " + str(sectionObstacleList[0]) + ", second obsacle: " + str(sectionObstacleList[1]))
    
    dC.brake()
    # parser.setTowerAngle(0)
    if parser.obstacles[2] == parser.RED:
        dC.driveToWall(speedStraightVerySlow,90,800,dC.frontWall)
        dC.brake()
        dC.tightTurn(speedCurveSlow,0)
        dC.brake()
        if prevSectionObstacleList[1] == parser.GREEN:
            dC.driveDist(speedStraightSlow, 0, 300)
        dC.driveToWall(speedStraightVerySlow, 0, 180, wallDir=dC.leftWall)
        dC.driveDist(speedStraightSlow, 0, 150)
        dC.brake()
        dC.tightTurn(speedCurveSlow,-45)
        dC.brake()
        dC.tightTurn(-speedCurveSlow,-70)
        dC.brake()
        dC.tightTurn(speedCurveSlow,-90)
        dC.brake()
        dC.driveDist(-speedStraightSlow, -90, 300)
        dC.driveToWall(-speedStraightSlow, -90, 300, wallDir=dC.backWall)
        dC.brake()
        dC.tightTurn(-speedCurveSlow, 0)
        dC.brake()
    else:
        dC.driveToWall(speedStraightSlow,90,440,dC.frontWall) #dist = 400
        dC.brake()
        dC.tightTurn(speedCurveSlow,0)
        dC.brake()
        if prevSectionObstacleList[1] == parser.GREEN:
            dC.driveDist(speedStraightSlow, 0, 300)
        dC.driveToWall(speedStraightVerySlow, 0, 180, wallDir=dC.leftWall)
        dC.driveDist(speedStraightVerySlow, 0, 150)
        dC.brake()
        dC.tightTurn(speedCurveSlow, -90)
        dC.brake()
        dC.driveToWall(-speedStraightSlow, -90, 300, wallDir=dC.backWall)
        dC.brake()
        dC.tightTurn(-speedCurveSlow, 0)
        dC.brake()

def parkCCW(parser: Parser, dC: DriveController, sectionObstacleList):
    """@brief Perform the final parallel-parking maneuver for a CCW run.

    @param parser              Parser with the scanned obstacle layout.
    @param dC                  DriveController providing motion primitives.
    @param sectionObstacleList list of obstacle colors in the parking section.
    @return None
    """
    speedStraight=1
    speedStraightSlow=0.6
    speedStraightVerySlow=0.3
    speedCurve=1
    speedCurveSlow=0.6
    speedCurveVerySlow=0.3
    
    print("First obstacle: " + str(sectionObstacleList[0]) + ", second obsacle: " + str(sectionObstacleList[1]))
    dC.brake()
    # parser.setTowerAngle(270)
    if sectionObstacleList[0] == parser.GREEN:
        # dC.driveToWall(speedStraightVerySlow, 0, 240, wallDir=dC.rightWall)
        # dC.driveDist(speedStraightVerySlow, 0, 100)
        dC.driveDist(-speedStraightSlow, 0, 100)
        dC.brake()
        dC.tightTurn(speedCurveSlow,90)
        dC.driveToWall(speedStraightSlow,90,400,dC.frontWall)
        dC.tightTurn(speedCurveSlow,0)
    else:
        dC.driveDist(speedStraight, 0, 400)
    dC.brake()
    dC.tightTurn(speedCurveVerySlow, 0)
    dC.driveToWall(speedStraightVerySlow,0,1050, 900)
    dC.brake()
    # dC.driveDist(-speedStraightVerySlow, 0, 150)
    dC.driveDist(-speedStraightVerySlow, 0, 100)
    dC.brake()
    # dC.driveToWall(-speedStraightVerySlow, 0, 180, wallDir=dC.rightWall)
    # dC.brake()
    # dC.driveDist(speedStraightSlow, 0, 150)
    # dC.brake()
    dC.tightTurn(speedCurveSlow, -90)
    dC.brake()
    dC.driveToWall(-speedStraightSlow, -90, 300, wallDir=dC.backWall)
    dC.brake()
    dC.tightTurn(-speedCurveSlow, 0)
    dC.brake()

def detectObstaclesCCW(parser: Parser, cam: Camera):
    """@brief Scan the whole course for obstacles from the start (CCW layout).

    Rotates the camera tower to three fixed angles, captures an image at each
    and fills `parser.obstacles[0..11]` with the detected colors.
    @param parser Parser whose obstacle array is populated.
    @param cam    Camera used to capture and analyze each view.
    @return None
    """
    sleepTime = 0.5
    
    parser.setTowerAngle(180)
    time.sleep(sleepTime)
    cam.captureImage()
    
    parser.obstacles[2] = cam.getObstacles("CCW", 2)
    parser.obstacles[3] = cam.getObstacles("CCW", 3)
    
    if parser.obstacles[3] is None:
        parser.obstacles[4] = cam.getObstacles("CCW", 4)
    else:
        parser.obstacles[4] = None
    
    if parser.obstacles[4] is None:
        parser.obstacles[5] = cam.getObstacles("CCW", 5)
    else:
        parser.obstacles[5] = None
        
    parser.setTowerAngle(225)
    time.sleep(sleepTime)
    cam.captureImage()
    
    parser.obstacles[1] = cam.getObstacles("CCW", 1)
    parser.obstacles[6] = cam.getObstacles("CCW", 6)
    parser.obstacles[7] = cam.getObstacles("CCW", 7)
    parser.obstacles[8] = cam.getObstacles("CCW", 8)
    
    parser.setTowerAngle(270)
    time.sleep(sleepTime)
    cam.captureImage()
    
    parser.obstacles[0] = cam.getObstacles("CCW", 0)
    parser.obstacles[9] = cam.getObstacles("CCW", 9)
    parser.obstacles[10] = cam.getObstacles("CCW", 10)
    parser.obstacles[11] = cam.getObstacles("CCW", 11)
    
    parser.setTowerAngle(130)
    for i in range(12):
        print(f"{i}: {parser.colorName(parser.obstacles[i])}")
        
    call("sudo systemctl restart smbd", shell=True)
    
def detectObstaclesCW(parser: Parser, cam: Camera):
    """@brief Scan the whole course for obstacles from the start (CW layout).

    Rotates the camera tower to three fixed angles, captures an image at each
    and fills `parser.obstacles[0..11]` with the detected colors.
    @param parser Parser whose obstacle array is populated.
    @param cam    Camera used to capture and analyze each view.
    @return None
    """
    sleepTime = 0.5
        
    parser.setTowerAngle(90)
    time.sleep(sleepTime)
    cam.captureImage()
    
    parser.obstacles[0] = cam.getObstacles("CW", 0)
    parser.obstacles[1] = cam.getObstacles("CW", 1)
    parser.obstacles[9] = cam.getObstacles("CW", 9)
    parser.obstacles[10] = cam.getObstacles("CW", 10)
    parser.obstacles[11] = cam.getObstacles("CW", 11)
    
    parser.setTowerAngle(45)
    time.sleep(sleepTime)
    cam.captureImage()

    parser.obstacles[6] = cam.getObstacles("CW", 6)
    parser.obstacles[7] = cam.getObstacles("CW", 7)
    parser.obstacles[8] = cam.getObstacles("CW", 8)
    
    parser.setTowerAngle(20)
    time.sleep(sleepTime)
    cam.captureImage()
    
    parser.obstacles[2] = cam.getObstacles("CW", 2)
    parser.obstacles[3] = cam.getObstacles("CW", 3)
    
    if parser.obstacles[3] is None:
        parser.obstacles[4] = cam.getObstacles("CW", 4)
    else:
        parser.obstacles[4] = None
    
    if parser.obstacles[4] is None:
        parser.obstacles[5] = cam.getObstacles("CW", 5)
    else:
        parser.obstacles[5] = None
    
    parser.setTowerAngle(135)
    for i in range(12):
        print(f"{i}: {parser.colorName(parser.obstacles[i])}")
        
    call("sudo systemctl restart smbd", shell=True)  

def findDirection(parser: Parser, dC: DriveController):
    """@brief Determine whether the course is run clockwise or counter-clockwise.

    Waits until one side sensor sees a near wall and sets `parser.Direction`
    accordingly (near right wall => CCW, otherwise CW).
    @param parser Parser whose Direction field is set.
    @param dC     DriveController providing sensor access and logging.
    @return None
    """
    distRight = 0
    distLeft = 0
    
    # Wait until a side wall comes within 400 mm; the near side tells us which
    # way around the track the car is pointing.
    while (distLeft > 400 or distLeft == 0) and (distRight > 400 or distRight == 0):
        distRight = dC.getDist([3,4],3,dC.rightWall)
        distLeft = dC.getDist([3,4],3,dC.leftWall)
    
    print(f"Distance right: {distRight}, Distance left: {distLeft}")
    dC.logger.log(f"Obstacel Challenge Single Distance right: {distRight}, Distance left: {distLeft}")
    dC.logger.logTof(parser, parser.leftSensor)
    dC.logger.logTof(parser, parser.rightSensor)
    
    
    if distRight >0 and distRight < 400:
        print("counterClockwise")
        dC.logger.log("Obstacle Challenge: counterClockwise")
        parser.Direction = parser.CCW
    else:
        print("Clockwise")
        dC.logger.log("Obstacle Challenge: clockwise")
        parser.Direction = parser.CW

def FirstObstacle(parser: Parser, dC: DriveController, sectionObstacleList, i):
    """@brief Drive past the first obstacle of a section.

    Passes a green obstacle on the left and a red/unknown one on the right.
    @param parser              Parser with shared state.
    @param dC                  DriveController providing motion primitives.
    @param sectionObstacleList list of obstacle colors in the current section.
    @param i                   int section counter within the lap.
    @return None
    """
    speedStraight = dC.topSpeed
    speedCurve=1
    
    if i == 3:
        wallDriveDist = 600
    else:
        wallDriveDist = 450
        
    print("Obstacle:", parser.colorName(parser.checkSection(dC.section)))
    
    if sectionObstacleList[0] == parser.GREEN:
        dC.turn(speedCurve,0)
        dC.driveAwayFromWall(speedStraight, 0, 1000)
        
    elif sectionObstacleList[0] in (parser.RED, None):
        print(f"Color thingy: {parser.colorName(parser.checkSection(dC.prevSection()))}")
        dC.driveToWall(speedStraight,90,wallDriveDist)
        dC.turn(speedCurve,0)
        dC.driveAwayFromWall(speedStraight, 0, 1000)

def SameObstacles(parser: Parser, dC: DriveController, sectionObstacleList, nextSectionObstacleList, mirror):
    """@brief Cross a section whose two obstacles share the same color.

    Drives straight to the far wall while optionally avoiding a side wall,
    with a recovery move if it overshoots past a following green obstacle.
    @param parser                  Parser with shared state.
    @param dC                      DriveController providing motion primitives.
    @param sectionObstacleList     list of obstacle colors in this section.
    @param nextSectionObstacleList list of obstacle colors in the next section.
    @param mirror                  bool True for a clockwise (mirrored) run.
    @return None
    """
    speedStraight = dC.topSpeed
    
    wall = dC.rightWall if mirror else dC.leftWall
    
    if sectionObstacleList[0] == parser.GREEN:
        wallLost = dC.driveToWall(speedStraight,0,1050,900,avoidWall=wall,minTravel=750) #1050, 900
        # drove to far (past the next obstacle):
        if wallLost and nextSectionObstacleList[0] == parser.GREEN:
            dC.brake()
            # dC.driveAwayFromWall(-0.5,0,900,dC.frontWall)
            dC.driveDist(-0.5,0,600)
            print("Dir: " + str(dir))
            dC.driveToWall(-0.5,0,300,wallDir=dC.convertDir(parser, dC.leftWall))
            dC.brake()
            dC.driveToWall(0.5,0,300,wallDir=dC.convertDir(parser, dC.leftWall))
            dC.driveDist(0.5,0,200)
            dC.brake()

    elif sectionObstacleList[0] in (parser.RED, None):
        dC.driveToWall(speedStraight,0,1050,900, avoidWall=None, minTravel=750)

def SecondObstacle(parser: Parser, dC: DriveController, sectionObstacleList, i):
    """@brief Handle the second, differently-colored obstacle of a section.

    Advances a bit then performs a lane change around the appropriate wall
    depending on the green->red or red->green color order.
    @param parser              Parser with shared state.
    @param dC                  DriveController providing motion primitives.
    @param sectionObstacleList list of obstacle colors in this section.
    @param i                   int section counter within the lap.
    @return None
    """
    speedStraight = dC.topSpeed
    speedCurve=1
    
    if sectionObstacleList[0] == parser.GREEN and sectionObstacleList[1] == parser.RED:
        dC.driveDist(speedStraight, 0, 300)
        wallDrive(parser, dC, dC.rightWall, speedCurve, speedStraight, 90, i)
    
    else: # Red -> Green
        dC.driveDist(speedStraight, 0, 300)
        wallDrive(parser, dC, dC.leftWall, speedCurve, speedStraight, 90)

def obstacleChallenge(parser: Parser, dC: DriveController, cam: Camera):
    """@brief Run the full obstacle challenge (full-scan, fixed-route strategy).

    Determines the direction, scans all obstacles up front, unparks, then
    drives three laps reacting to the stored obstacle layout and finally
    parks in the start zone.
    @param parser Parser with shared state and obstacle array.
    @param dC     DriveController providing motion primitives.
    @param cam    Camera used for the initial obstacle scan.
    @return None
    """
    speedStraight = dC.topSpeed
    speedCurve=1
    speedCurveSlow=0.65
    
    # parser.obstacles[0] = parser.RED
    # parser.obstacles[2] = parser.RED
    
    # parser.obstacles[3] = parser.RED
    # parser.obstacles[5] = parser.RED
    
    # parser.obstacles[6] = parser.RED
    # parser.obstacles[8] = parser.RED
    
    # parser.obstacles[9] = parser.RED
    # parser.obstacles[11] = parser.RED
    
    findDirection(parser, dC)
    mirror = False
    if parser.Direction == parser.CW:
        mirror = True
        detectObstaclesCW(parser, cam)
        unParkCW(parser, dC)
    else:
        mirror = False
        detectObstaclesCCW(parser, cam)
        unParkCCW(parser, dC)
    
    dC.section += 1
    # Three laps x four sections. Each iteration handles one section: pass its
    # first obstacle, then either cross (same colors) or weave to the second.
    for j in range(3):
        for i in range(4):
            lastSection = i == 3 and j == 2
            secondToLastSection = i == 2 and j == 2
            sectionObstacleList = parser.checkSectionMulti(dC.section, mirror, mirror)
            nextSectionObstacleList = parser.checkSectionMulti(dC.nextSection(), mirror, mirror)
            parked = False
            
            if secondToLastSection and parser.Direction == parser.CW:
                dC.topSpeed = 1          # slow down before the CW parking approach
             
            if lastSection and parser.Direction == parser.CW:
                parkCW(parser, dC)
                parked = True
            else:
                FirstObstacle(parser, dC, sectionObstacleList, i)
                if lastSection:
                    parkCCW(parser, dC, sectionObstacleList)
                    parked = True
            
            # Same color on both slots -> straight crossing; otherwise weave
            # around the second, differently-colored obstacle.
            if sectionObstacleList[0] == sectionObstacleList[1] and not parked:
                SameObstacles(parser, dC, sectionObstacleList, nextSectionObstacleList, mirror)
            elif not parked:
                SecondObstacle(parser, dC, sectionObstacleList, i)
            
            dC.section = dC.nextSection()
            
            if dC.end():
                print("\n--------------------- END --------------------\n")
                return
            
            print("!!!!!!!!!!!!!!!!!!!!! DONE !!!!!!!!!!!!!!!!!!!!")
        parser.round += 1
        print("********************* Super DONE ********************")
    
    parser.endTime = time.time()
    dC.brake()