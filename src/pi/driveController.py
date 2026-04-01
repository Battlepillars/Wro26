import time

class DriveController:
    def __init__(self, parser):
        self.acceleration = 0.2
        self.deacceleration = 0.2
        self.setpoint = 0
        self.targetSpeed = 0
        self.lastTime = 0
        self.parser = parser
    
    def driveSpeed(self, speed):
        self.targetSpeed = speed
        while True:
            self.calcAccel()
            

    def calcAccel(self):
        lastCycleTime = time.time() - self.lastTime
        frq = 0.01

        if (lastCycleTime) < frq:
            time.sleep(frq-lastCycleTime)
        self.lastTime = time.time()

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
        
        self.parser.setSpeed(self.setpoint)
        