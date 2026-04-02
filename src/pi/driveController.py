import time

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

class DriveController:
    def __init__(self, parser, stop_event, checkVoltage):
        self.acceleration = 0.5
        self.deacceleration = 0.5
        self.setpoint = 0
        self.targetSpeed = 0
        self.targetHeading = 0
        self.lastTime = 0
        self.parser = parser
        self.stop_event = stop_event
        self.pidSteer = PIDController(Kp=2, Ki=0, Kd=0, setpoint=0, min=-90, max=90)
        self.checkVoltage = checkVoltage
    
    def end(self):
        if self.stop_event.is_set():
            self.parser.setSpeed(0)
            self.parser.setSteer(90)
            return True
        return False
        

    def driveDist(self, speed, heading, dist):
        startDist = self.parser.distance
        self.targetSpeed = speed
        self.heading = heading
        while self.parser.distance-startDist < dist and not self.stop_event.is_set():
            # print(self.parser.distance-startDist)
            self.calcAccel()
        if self.end():
            return
        self.brake()
    
    def brake(self):
        self.targetSpeed = 0
        while self.parser.speed > 0 and not self.stop_event.is_set():
            self.calcAccel()
        if self.end():
            return


    def driveSpeed(self, speed, heading):
        self.targetSpeed = speed
        self.heading = heading
        while not self.stop_event.is_set():
            self.calcAccel()
        if self.end():
            return
            

    def calcAccel(self):
        lastCycleTime = time.time() - self.lastTime
        frq = 0.01

        if (lastCycleTime) < frq:
            time.sleep(frq-lastCycleTime)
        self.lastTime = time.time()



        errorAngle = -self.targetHeading + self.parser.gyro.euler[0]
        
        while errorAngle > 180:
            errorAngle -= 360
        while errorAngle < -180:
            errorAngle += 360
        
        outputSteer = -(self.pidSteer.compute(errorAngle,1))+90

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
            self.parser.setSteer(outputSteer)
        