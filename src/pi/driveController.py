import time
import math

from parser import Parser

class DriveController:
    logCountetr = 0
    
    backWall = 4
    rightWall = 5
    frontWall = 1
    leftWall = 3
    angleLeftWall = 0
    angleRightWall = 2
    auto = 0
    turnRight = 1
    turnLeft = 2
    smallest = 0
    biggest = 1
    
    def __init__(self, parser: Parser, stop_event):
        DriveController.angleLeftWall = parser.angleLeftSensor
        DriveController.angleRightWall = parser.angleRightSensor
        DriveController.frontWall = parser.frontSensor
        DriveController.rightWall = parser.rightSensor
        DriveController.leftWall = parser.leftSensor
        DriveController.backWall = parser.backSensor
        self.acceleration = 1
        self.deacceleration = 8
        self.setpoint = 0
        self.targetSpeed = 0
        self.targetHeading = 0
        self.lastTime = 0
        self.section = 0
        self.turnDir = self.auto
        self.parser = parser
        self.stop_event = stop_event
        self.pidSteer = PIDController(Kp=1, Ki=0, Kd=0, setpoint=0, min=-90, max=90)
        self.pidSteer2 = PIDController(Kp=0.5, Ki=0, Kd=0, setpoint=0, min=-90, max=90)
    
    def end(self):
        if self.stop_event.is_set():
            self.parser.endTime = time.time()
            self.parser.setSpeed(0)
            self.parser.setSteer(90)
            return True
        return False
    
    # start helper functions:
    
    def getDist(self, poses:list, row, wallDir = frontWall, mode = biggest):
        val = 0
        tempVal = 0
        for i in poses:
            tempVal = self.parser.camValues[wallDir][i+row*8]
            if mode == self.biggest and tempVal > val:
                val = tempVal
            elif mode == self.smallest and tempVal < val and tempVal > 0:
                val = tempVal
        return val

    def nextSection(self):
        """ returns current section +1 """
        if self.section < 3:
            return self.section+1
        else:
            return 0
    
    def setCommand(self, command):
        self.parser.currentCommand = command
    
    def setSpeed(self, speed):
        self.targetSpeed = speed
    
    def setTargetHeading(self, heading):
        heading += self.section*-90         # rotating to match current section
        while heading > 180:
            heading -= 360
        while heading < -180:
            heading += 360
        self.targetHeading = heading
    
    # end helper functions
    
    def customTurn(self, speed, angle, dist):
        self.setCommand("customTurn")
        self.setSpeed(speed)
        
        self.parser.setSteer(angle)
        
        startDist = self.parser.distance
        
        while self.parser.distance-startDist < dist and not self.stop_event.is_set():
            print(f"CustomTurn: Angle: {angle} Dist: {dist} CurrenDist: {self.parser.distance-startDist}")
            self.calcAccel(False)
        if self.end():
            return
    
    def quickTurn(self, speed, heading, turnDir = auto):
        self.setCommand("Quick turn")
        self.setSpeed(speed)
        self.setTargetHeading(heading)
        self.turnDir = turnDir
        
        errorAngle = 500

        print("Quick Turn: ","Error:",errorAngle,"\tSpeed:",self.parser.speed,"Target heading:",self.targetHeading)

        while abs(errorAngle) > 5 and not self.stop_event.is_set():
            errorAngle = self.parser.gyro.euler[0] - self.targetHeading
            
            while errorAngle > 180:
                errorAngle -= 360
            while errorAngle < -180:
                errorAngle += 360
            
            # doPid = abs(errorAngle)<10*(speed*self.parser.speed*2)
            doPid = abs(errorAngle)<20
            
            self.logCountetr += 1
            if self.logCountetr %3==0 or True:
                print("Quick Turn: ","Error:",errorAngle,"\tDopid:",doPid,"Speed:",self.parser.speed,"Target heading:",self.targetHeading)
            
            self.calcAccel(doPid,2)
            if not doPid:
                if errorAngle < 0:
                    self.parser.setSteer(0)
                else:
                    self.parser.setSteer(180)

        if self.end():
            return
    
    def turn(self, speed, heading, turnDir = auto):
        self.setCommand("turn")
        self.setSpeed(speed)
        self.setTargetHeading(heading)
        self.turnDir = turnDir
        
        errorAngle = 5
        
        while abs(errorAngle) > 2 and not self.stop_event.is_set():
            errorAngle = self.parser.gyro.euler[0] - self.targetHeading
            
            while errorAngle > 180:
                errorAngle -= 360
            while errorAngle < -180:
                errorAngle += 360
            
            # doPid = abs(errorAngle)<10*(speed*self.parser.speed*2)
            doPid = abs(errorAngle)<50
            
            self.logCountetr += 1
            if self.logCountetr %3==0 or True:
                print("Turn: ","Error:",errorAngle,"\tDopid:",doPid,"Speed:",self.parser.speed,"Target heading:",self.targetHeading)
            
            self.calcAccel(doPid,2)
            if not doPid:
                if errorAngle < 0:
                    self.parser.setSteer(0)
                else:
                    self.parser.setSteer(180)

        if self.end():
            return
    
    def driveToWall(self, speed, heading, dist, wallDir = frontWall, bigVisionRange = False):
        self.setCommand("driveToWall")
        self.setSpeed(speed)
        self.setTargetHeading(heading)
        
        lastVal = 10000
        
        while lastVal > (dist+20) and not self.stop_event.is_set():
            self.calcAccel()
            if bigVisionRange:
                val = self.getDist([0,1,2,3,4,5,6,7],3,wallDir)
            else:
                val = self.getDist([3,4],3,wallDir)
            
            self.logCountetr += 1
            if val > 0:
                lastVal = val
            if lastVal is not None: #self.logCountetr %3==0 and 
                print("ToWall: "+str(lastVal),"Heading:",heading)
        if self.end():
            return
    
    def driveAwayFromWall(self, speed, heading, dist, wallDir = backWall):
        self.setCommand("driveAwayFromWall")
        self.setSpeed(speed)
        self.setTargetHeading(heading)
        
        
        noWallCount = 0
        pos1 = 3+4*8
        pos2 = 4+4*8
        val = max(self.parser.camValues[wallDir][pos1],self.parser.camValues[wallDir][pos2])
        
        
        while noWallCount < 3 and not self.stop_event.is_set():
            self.calcAccel()
            val = max(self.parser.camValues[wallDir][pos1],self.parser.camValues[wallDir][pos2])
        
            if val <= 0 or val > dist:
                noWallCount += 1
            elif noWallCount > 0:
                noWallCount -= 1
            print("away: "+str(val) + " " + str(noWallCount))

        if self.end():
            return
    
    def driveAlongWall(self, speed, heading, wallDir = rightWall):
        self.setCommand("driveAlongWall")
        self.setSpeed(speed)
        self.setTargetHeading(heading)
        
        
        noWallCount = 0
        pos1 = 3+3*8
        pos2 = 4+3*8
        
        while noWallCount < 1 and not self.stop_event.is_set():
            self.calcAccel()
            val = max(self.parser.camValues[wallDir][pos1],self.parser.camValues[wallDir][pos2])
            
            if val <= 0 or val > 1000:
                noWallCount += 1
            elif noWallCount > 0:
                noWallCount -= 1
            print(str(val) + " " + str(noWallCount))
        if self.end():
            return
    
    def driveDist(self, speed, heading, dist):
        self.setCommand("driveDist")
        startDist = self.parser.distance
        self.setSpeed(speed)
        self.setTargetHeading(heading)
        while self.parser.distance-startDist < dist and not self.stop_event.is_set():
            print(f"DriveDist: Dist: {dist} CurrenDist: {self.parser.distance-startDist}")
            self.calcAccel()
        if self.end():
            return
    
    def brake(self):
        self.setSpeed(0)
        self.parser.setSteer(90)
        
        while self.parser.speed > 0 and not self.stop_event.is_set():
            self.calcAccel(False)
            print("Brake: "+str(self.parser.speed))
        if self.end():
            return


    def driveSpeed(self, speed, heading):
        self.setCommand("driveSpeed")
        self.setSpeed(speed)
        self.setTargetHeading(heading)
        while not self.stop_event.is_set():
            self.calcAccel()
        if self.end():
            return
        

    def calcAccel(self, steer = True, pid = 0):
        lastCycleTime = time.time() - self.lastTime
        frq = 0.01

        if (lastCycleTime) < frq:
            time.sleep(frq-lastCycleTime)
        self.lastTime = time.time()


        if steer:
            errorAngle = -self.targetHeading + self.parser.gyro.euler[0]
            
            while errorAngle > 180:
                errorAngle -= 360
            while errorAngle < -180:
                errorAngle += 360
            
            if pid == 0:
                outputSteer = -(self.pidSteer.compute(errorAngle,1))+90
            elif pid == 2:
                outputSteer = -(self.pidSteer2.compute(errorAngle,1))+90

        if self.setpoint < self.targetSpeed and self.setpoint >= 0:     # nach vorne Beschleunigen
            self.setpoint += self.acceleration * frq
            if self.setpoint > self.targetSpeed:
                self.setpoint = self.targetSpeed
        
        elif self.setpoint > self.targetSpeed and self.setpoint <= 0:   # nach hinten Beschleunigen
            self.setpoint -= self.acceleration * frq
            if self.setpoint < self.targetSpeed:
                self.setpoint = self.targetSpeed
        
        elif self.setpoint < self.targetSpeed and self.setpoint <= 0:   # nach hinten Bremsen
            self.setpoint += self.deacceleration * frq
            if self.setpoint > self.targetSpeed:
                self.setpoint = self.targetSpeed
        
        elif self.setpoint > self.targetSpeed and self.setpoint >= 0:   # nach vorne Bremsen
            self.setpoint -= self.deacceleration * frq
            if self.setpoint < self.targetSpeed:
                self.setpoint = self.targetSpeed
        
        if not self.stop_event.is_set():
            self.parser.setSpeed(self.setpoint)
            if steer:
                self.parser.setSteer(outputSteer)


class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint, min, max, drive = 0):
        """@brief Initialize a PID controller instance.

        @param Kp float Proportional gain.
        @param Ki float Integral gain.
        @param Kd float Derivative gain.
        @param setpoint float Target value the controller drives toward.
        @param min float Minimum output clamp.
        @param max float Maximum output clamp.
        @param drive int Optional flag (1 if used for drive motor diagnostics).
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.previous_error = 0
        self.integral = 0
        self.min = min
        self.max = max
        self.drive = drive
    def reset(self):
        """@brief Reset accumulated integral and derivative history.

        Call when direction changes or large setpoint jump occurs to avoid
        stale integral causing windup.
        @return None
        """
        self.previous_error = 0
        self.integral = 0
        

    def compute(self, process_variable, dt, slam=None):
        """@brief Compute PID output for current process variable.

        Applies anti-windup clamping for integral term then combines P,I,D.
        @param process_variable float Current measured value.
        @param dt float Elapsed time (seconds) since last compute.
        @param slam Slam|None Optional slam object for extended diagnostics.
        @return float Controller output within [min,max].
        """
        # Calculate error
        error = self.setpoint - process_variable
        
        # if (self.drive == 1) and (slam != None):
        #     if len(slam.errorDriveList) > 41:
        #         slam.errorDriveList.pop(0)
        #     slam.errorDriveList.append(1 - (process_variable/self.setpoint))
        #     # print("errorDriveList: ", slam.errorDriveList, " mean: ", statistics.mean(slam.errorDriveList), " speed: ", slam.speed)
        #     if (statistics.mean(slam.errorDriveList) > 0.9) and (slam.speed < 0.1) and (len(slam.errorDriveList) > 40):
        #         slam.crash = 1
        
        # Proportional term
        P_out = self.Kp * error
        
        # Integral term
        self.integral += error * dt
        
        if self.Ki * self.integral > self.max:
            self.integral = self.max / self.Ki
        if self.Ki * self.integral < self.min:
            self.integral = self.min / self.Ki
        I_out = self.Ki * self.integral
        
        # Derivative term
        derivative = (error - self.previous_error) / dt
        D_out = self.Kd * derivative
        
        # Compute total output
        output = P_out + I_out + D_out
        
        # Update previous error
        self.previous_error = error
        if output > self.max:
            output = self.max
        if output < self.min:
            output = self.min
        
        # if (self.drive == 1) and (slam != None):
        #     if len(slam.errorDriveList) > 100:
        #         slam.errorDriveList.pop(0)
        #     slam.errorDriveList.append(output)
        #     # print("errorDriveList: ", slam.errorDriveList, " mean: ", statistics.mean(slam.errorDriveList), " speed: ", slam.speed)
        #     if (statistics.mean(slam.errorDriveList) > (self.max/1.2)) and (slam.speed < 0.2) and (len(slam.errorDriveList) > 100):
        #         slam.crash = 1
        
        return output