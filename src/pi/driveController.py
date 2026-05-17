import time
import math

from parser import Parser
from logger import Logger
from subprocess import call

class DriveController:
    """High-level motion helper for heading, speed, and wall-relative maneuvers."""

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
    firstEnd = 0
    
    def __init__(self, parser: Parser, stop_event, logger: Logger = None):
        """Initialize controller state and bind it to the live parser sensors and logger."""
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
        self.logger = logger if logger is not None else Logger()
    
    def end(self):
        """Stop the vehicle and report whether the external stop event requested shutdown."""
        if self.stop_event.is_set():
            self.parser.setSpeed(0)
            self.parser.setSteer(90)
            if self.parser.endTime == 0:
                self.parser.endTime = time.time()
            if DriveController.firstEnd == 0:
                call("sudo systemctl restart smbd", shell=True)
                DriveController.firstEnd = 1
            return True
        return False
    
    # start helper functions:
    
    def getDist(self, poses:list, row, wallDir = frontWall, mode = biggest):
        """Return the selected distance sample from one camera row across the given column indices."""
        val = 0
        tempVal = 0
        for i in poses:
            tempVal = self.parser.camValues[wallDir][i+row*8]
            if mode == self.biggest and tempVal > val:
                val = tempVal
            elif mode == self.smallest and tempVal < val and tempVal > 0:
                val = tempVal
        return val

    def wallToString(self, wall):
        if wall == self.frontWall:
            return "front wall"
        elif wall == self.rightWall:
            return "right wall"
        elif wall == self.leftWall:
            return "left wall"
        elif wall == self.backWall:
            return "back wall"
        elif wall == self.angleLeftWall:
            return "angle left wall"
        elif wall == self.angleRightWall:
            return "angle right wall"
        else:
            return "unknown wall"

    def nextSection(self):
        """Return the next course section index, wrapping from section 3 back to 0."""
        if self.section < 3:
            return self.section+1
        else:
            return 0
    
    def prevSection(self):
        """Return the previous course section index, wrapping from section 0 back to 3."""
        if self.section > 0:
            return self.section-1
        else:
            return 3
    
    def setCommand(self, command):
        """Store the current high-level maneuver name on the parser for status reporting."""
        self.parser.currentCommand = command
    
    def setSpeed(self, speed):
        """Update the target drive speed that `calcAccel` ramps toward."""
        self.targetSpeed = speed
    
    def setTargetHeading(self, heading):
        """Normalize a heading into the current section and clamp it to [-180, 180]."""
        
        if self.parser.Direction == self.parser.CW:      # rotating to match current section
            heading = -heading + self.section*90   
        else:
            heading += self.section*-90       
        
        while heading > 180:
            heading -= 360
        while heading < -180:
            heading += 360
        self.targetHeading = heading
    
    def logStuff(self, message):
        self.logger.log(f"{message}, Section: {self.section}, Time: {time.time()-self.parser.startTime:.2f}")
    
    # end helper functions
    
    def customTurn(self, speed, angle, dist):
        """Drive a fixed steering angle until the requested travel distance has been covered."""
        self.setCommand("customTurn")
        self.setSpeed(speed)
        self.parser.setSteer(angle)
        
        startDist = self.parser.distance
        
        while abs(self.parser.distance-startDist) < dist and not self.stop_event.is_set():
            self.logStuff(f"CustomTurn: Angle: {angle}, Dist: {dist}, CurrenDist: {self.parser.distance-startDist:.0f}")
            self.calcAccel(False)
        if self.end():
            return
    
    
    def tightTurn(self, speed, heading, turnDir = auto):
        """Turn tight toward a target with maximum steering, slowing down as it approaches the target heading."""
        self.setCommand("Tight turn")
        self.setSpeed(speed)
        self.setTargetHeading(heading)
        self.turnDir = turnDir
        
        errorAngle = 500

        self.logStuff(f"Quick Turn: Error:{errorAngle:.0f}, Speed:{self.parser.speed:.2f}, Target heading:{self.targetHeading}")

        while abs(errorAngle) > 5 and not self.stop_event.is_set():
            errorAngle = self.parser.getHeading() - self.targetHeading
            
            while errorAngle > 180:
                errorAngle -= 360
            while errorAngle < -180:
                errorAngle += 360
            
            if (errorAngle>0) ==(speed>0):
                self.parser.setSteer(180)
            else:                
                self.parser.setSteer(0)
            
            mySpeed=speed
            
            if abs(errorAngle) < 60:
                mySpeed = speed*(abs(errorAngle-20)/40)
            if abs(errorAngle) < 25:
                mySpeed = 0.1 * (speed/abs(speed))
            if abs(errorAngle) < 10:
                mySpeed = 0.05 * (speed/abs(speed))
            if abs(mySpeed) < 0.05:
                mySpeed = 0.05 * (speed/abs(speed))
            self.setSpeed(mySpeed)
            self.logCountetr += 1
            if self.logCountetr %3==0 or True:
                self.logStuff(f"Tight Turn: Error:{errorAngle:.0f},  Speed:{mySpeed:.2f}, Actual Speed:{self.parser.speed:.2f}, Target heading:{self.targetHeading}")
            
            self.calcAccel(False,0)

        if self.end():
            return    
    
    def quickTurn(self, speed, heading, turnDir = auto):
        """Turn aggressively toward a target heading, switching to PID steering near the target."""
        self.setCommand("Quick turn")
        self.setSpeed(speed)
        self.setTargetHeading(heading)
        self.turnDir = turnDir
        
        errorAngle = 500

        self.logStuff(f"Quick Turn: Error:{errorAngle:.0f}, Speed:{self.parser.speed:.2f}, Target heading:{self.targetHeading}")

        while abs(errorAngle) > 5 and not self.stop_event.is_set():
            errorAngle = self.parser.getHeading() - self.targetHeading
            
            while errorAngle > 180:
                errorAngle -= 360
            while errorAngle < -180:
                errorAngle += 360
            
            # doPid = abs(errorAngle)<10*(speed*self.parser.speed*2)
            doPid = abs(errorAngle)<20
            
            self.logCountetr += 1
            if self.logCountetr %3==0 or True:
                self.logStuff(f"Quick Turn: Error:{errorAngle:.0f}, Dopid:{doPid}, Speed:{self.parser.speed:.2f}, Target heading:{self.targetHeading}")
            
            self.calcAccel(doPid,2)
            if not doPid:
                if errorAngle < 0:
                    self.parser.setSteer(0)
                else:
                    self.parser.setSteer(180)

        if self.end():
            return
    
    def turn(self, speed, heading, turnDir = auto):
        """Turn toward a target heading with a wider PID handoff and tighter finish tolerance."""
        self.setCommand("turn")
        self.setSpeed(speed)
        self.setTargetHeading(heading)
        self.turnDir = turnDir
        
        errorAngle = 5
        
        while abs(errorAngle) > 2 and not self.stop_event.is_set():
            errorAngle = self.parser.getHeading() - self.targetHeading
            
            while errorAngle > 180:
                errorAngle -= 360
            while errorAngle < -180:
                errorAngle += 360
            
            # doPid = abs(errorAngle)<10*(speed*self.parser.speed*2)
            doPid = abs(errorAngle)<50
            
            self.logCountetr += 1
            if self.logCountetr %3==0 or True:
                self.logStuff(f"Turn: Error:{errorAngle:.0f}, Dopid:{doPid}, Speed:{self.parser.speed:.2f}, Target heading:{self.targetHeading}")
            
            self.calcAccel(doPid,2)
            if not doPid:
                if errorAngle < 0:
                    self.parser.setSteer(0)
                else:
                    self.parser.setSteer(180)

        if self.end():
            return
    
    def driveToWall(self, speed, heading, dist, minDist = 0, wallDir = frontWall, bigVisionRange = False):
        """Drive toward a wall until camera depth reports the requested clearance."""
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
            if val > 0 and val >= minDist:
                lastVal = val
            if lastVal is not None: #self.logCountetr %3==0 and 
                self.logStuff(f"ToWall: {lastVal:.0f}, Dist: {dist}, Heading:{heading}")
        if self.end():
            return
    
    def driveAwayFromWall(self, speed, heading, dist, wallDir = backWall):
        """Drive away from a wall until rear camera samples no longer detect it within range."""
        self.setCommand("driveAwayFromWall")
        self.setSpeed(speed)
        self.setTargetHeading(heading)
        
        
        noWallCount = 0
        val = self.getDist([3,4],3,wallDir)
        
        
        while noWallCount < 3 and not self.stop_event.is_set():
            self.calcAccel()
            val = self.getDist([3,4],3,wallDir)
        
            if val <= 0 or val > dist:
                noWallCount += 1
            elif noWallCount > 0:
                noWallCount -= 1
            self.logStuff(f"Drive Away From Wall: {val}, Target Dist: {dist}, Heading: {heading}, NoWallCount: {noWallCount}")

        if self.end():
            return
    
    def driveAlongWall(self, speed, heading, wallDir = rightWall):
        """Follow a wall until the selected side camera samples indicate the wall is gone."""
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
            self.logStuff(f"Drive Along Wall: {val:.0f}, NoWallCount: {noWallCount}")
        if self.end():
            return
    
    def findeDirection(self, speed, heading):
        """Follow a wall until the the wall is gone."""
        self.setCommand("findeDirection")
        self.setSpeed(speed)
        self.setTargetHeading(heading)
        
        
        noWallLeftCount = 0
        noWallRightCount = 0
        
        
        while noWallLeftCount < 1 and noWallRightCount < 1 and not self.stop_event.is_set():
            self.calcAccel()
            leftVal = self.getDist([3,4],3,self.leftWall)
            rightVal = self.getDist([3,4],3,self.rightWall)
            
            if leftVal <= 0 or leftVal > 1000:
                noWallLeftCount += 1
            elif noWallLeftCount > 0:
                noWallLeftCount -= 1

            if rightVal <= 0 or rightVal > 1000:
                noWallRightCount += 1
            elif noWallRightCount > 0:
                noWallRightCount -= 1

            self.logStuff(f"Drive Along Wall: LeftVal: {leftVal:.0f}, RightVal: {rightVal:.0f}, NoWallLeftCount: {noWallLeftCount}, NoWallRightCount: {noWallRightCount}")
        self.end()
        if noWallLeftCount > noWallRightCount:
            self.parser.Direction = self.parser.CCW
            return self.leftWall
        else:
            self.parser.Direction = self.parser.CW
            return self.rightWall
    
    def driveDist(self, speed, heading, dist):
        """Drive straight for a measured encoder distance while holding the requested heading."""
        self.setCommand("driveDist")
        startDist = self.parser.distance
        self.setSpeed(speed)
        self.setTargetHeading(heading)
        while abs(self.parser.distance - startDist) < dist and not self.stop_event.is_set():
            self.logStuff(f"DriveDist: Dist: {dist}, CurrenDist: {self.parser.distance-startDist:.0f}, Heading: {heading}")
            self.calcAccel()
        if self.end():
            return
    
    def brake(self):
        """Ramp the target speed down to zero while keeping the steering centered."""
        self.setSpeed(0)
        self.parser.setSteer(90)
        
        while abs(self.parser.speed) > 0 and not self.stop_event.is_set():
            self.calcAccel(False)
            self.logStuff(f"Brake: {self.parser.speed:.2f}")
        if self.end():
            return


    def driveSpeed(self, speed, heading):
        """Hold a target speed and heading continuously until an external stop is requested."""
        self.setCommand("driveSpeed")
        self.setSpeed(speed)
        self.setTargetHeading(heading)
        while not self.stop_event.is_set():
            self.calcAccel()
        if self.end():
            return
        

    def calcAccel(self, steer = True, pid = 0,customAcc=0, customDeacc=0):
        """Run one control cycle: rate-limit, ramp speed, and optionally update steering PID output."""
        lastCycleTime = time.time() - self.lastTime
        frq = 0.01

        if (lastCycleTime) < frq:
            time.sleep(frq-lastCycleTime)
        self.lastTime = time.time()

        myAcc=self.acceleration
        myDeacc=self.deacceleration
        if customAcc != 0:
            myAcc = customAcc
        if customDeacc != 0:
            myDeacc = customDeacc

        if steer:
            errorAngle = -self.targetHeading + self.parser.getHeading()
            
            while errorAngle > 180:
                errorAngle -= 360
            while errorAngle < -180:
                errorAngle += 360
            
            if pid == 0:
                outputSteer = -(self.pidSteer.compute(errorAngle,1))+90
            elif pid == 2:
                outputSteer = -(self.pidSteer2.compute(errorAngle,1))+90

        if self.setpoint < self.targetSpeed and self.setpoint >= 0:     # nach vorne Beschleunigen
            self.setpoint += myAcc * frq
            if self.setpoint > self.targetSpeed:
                self.setpoint = self.targetSpeed
        
        elif self.setpoint > self.targetSpeed and self.setpoint <= 0:   # nach hinten Beschleunigen
            self.setpoint -= myAcc * frq
            if self.setpoint < self.targetSpeed:
                self.setpoint = self.targetSpeed
        
        elif self.setpoint < self.targetSpeed and self.setpoint <= 0:   # nach hinten Bremsen
            self.setpoint += myDeacc * frq
            if self.setpoint > self.targetSpeed:
                self.setpoint = self.targetSpeed
        
        elif self.setpoint > self.targetSpeed and self.setpoint >= 0:   # nach vorne Bremsen
            self.setpoint -= myDeacc * frq
            if self.setpoint < self.targetSpeed:
                self.setpoint = self.targetSpeed
        
        if not self.stop_event.is_set():
            self.parser.setSpeed(self.setpoint)
            if steer:
                if self.targetSpeed >= 0:
                    self.parser.setSteer(outputSteer)
                else:
                    self.parser.setSteer(180-outputSteer)


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