import serial # type: ignore
import subprocess
import time
import os
import json
import board # type: ignore
import busio # type: ignore
import adafruit_bno055 # type: ignore
from subprocess import call
from gyro85 import gyroBNO085


class Parser:
    RED = 0
    GREEN = 1
    
    amountSensors = 6
    leftSensor = 0
    frontSensor = 1
    rightSensor = 2
    backSensor = 3
    angleRightSensor = 4
    angleLeftSensor = 5
    CW = 0
    CCW = 1
    
    def __init__(self):
        for i in range(self.amountSensors):
            self.getPosForCam(i, setSensorIndex=True)

        self.camValues = []
        self.camValues = [[0 for _ in range(64)] for _ in range(self.amountSensors)]
        self.sensorCaptures = [0 for _ in range(self.amountSensors)]
        self.rps = 0
        self.count = 0
        self.output = 0
        self.setpoint = 0
        self.voltage = 12.6
        self.speed = 0
        self.distance = 0
        self.time = 0
        self.startTime = time.time()
        self.endTime = 0
        self.debugCam = False
        self.obstacles = []
        self.currentCommand = ""
        self.obstacles = [None for _ in range(12)]
        self.lastHeading = 0
        self.heading = 0
        self.round = 0
        self.Direction = Parser.CW
        self.button = False
        self.started = False


        # self.i2c = busio.I2C(board.SCL, board.SDA)
        # self.gyro = adafruit_bno055.BNO055_I2C(self.i2c, address=0x28)
        self.gyro85 = gyroBNO085()

        while not self.calibDone():
            print("Waiting for gyro calibration:", self.gyro.calibration_status)
            time.sleep(0.5)


        self.ser = serial.Serial()
        self.ser.port = "/dev/ttyAMA0"
        self.ser.baudrate = 921600
        self.ser.bytesize = 8
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.parity = serial.PARITY_NONE
        self.ser.open()


    def calibDone(self):
        return True
        # _, gyroCalibration, _, magnetometerCalibration = self.gyro.calibration_status
        # return gyroCalibration == 3

    def getHeading(self):
        # return self.gyro85.get_heading()
    
        # if not hasattr(self, 'gyro') or self.gyro is None:
        #     return 0
        
        # angle = self.gyro.euler[0]
        angle = self.gyro85.get_heading()
        
        if angle is None:
            angle = 0
        
        if self.Direction == self.CCW:
            if self.round == 0:
                angle += 0
            elif self.round == 1:
                angle += -3
            elif self.round == 2:
                angle += -6
        else:
            if self.round == 0:
                angle += 0
            elif self.round == 1:
                angle += 2
            elif self.round == 2:
                angle += 4
        
        return angle
        newHeading = self.gyro.euler[0]
        diff=newHeading - self.lastHeading
        if diff < -300:
            diff += 360
        elif diff > 300:
            diff -= 360

        cal=1.00 #1.0041667 # calibration factor to match the heading with the real rotation of the robot. (360/358.5)
                      # was calculated by comparing the gyro heading with the actual rotation of the robot. 
                      # The robot was rotated 10 times and the average difference between the gyro heading and the
                      # actual rotation was calculated to be 1.5 degrees per 360 degrees of rotation. This factor is used to correct the heading calculation.

        # if (diff>0):
        #     diff *= cal
        # else:
        #     diff /= cal

        diff *= cal     # the gyro turns not enough in  both directions, so the factor is applied to both positive and negative differences.

        self.heading += diff
        if (self.heading < 0):
            self.heading += 360 
        elif (self.heading >= 360):
            self.heading -= 360
        self.lastHeading = newHeading

        return self.heading
    def resetGyro(self):
        self.gyro85.reset_heading()
        # del self.gyro
        # self.lastHeading = 0
        # self.heading=0
        # self.gyro = adafruit_bno055.BNO055_I2C(self.i2c, address=0x28)
        # self.gyro.mode = adafruit_bno055.IMUPLUS_MODE
        # while not self.calibDone():
        #     print("Waiting for gyro calibration:", self.gyro.calibration_status)
        #     time.sleep(0.1)
        
    def sendReadySignal(self):
        self.send("ready,1\n")

    def sendStartSignal(self):
        self.send("start,1\n")

    def checkSection(self, section, mirror = False):
        if mirror:
            if section == 1:
                section = 3
            elif section == 3:
                section = 1
        
        for i in range(3):
            if self.obstacles[i+section*3] != None:
                return self.obstacles[i+section*3]
        return None

    def colorName(self, color):
        if color == self.RED:
            return "RED"
        if color == self.GREEN:
            return "GREEN"
        if color is None:
            return "NONE"
        return str(color)

    def assignMultibelObstacles(self, section, obstacleType, obstacles = [0,1,2]):
        for i in range(len(obstacles)):
            self.obstacles[i+section*3] = obstacleType

    def assignAllObstacles(self, colors: tuple):
        if len(colors) == 4:
            color1, color2, color3, color4 = colors
        else: 
            color1, color2, color3, color4, color4Left = colors
        
        if color4 is not None:
            self.obstacles[0] = color4
        else:
            self.obstacles[2] = color4Left
        self.assignMultibelObstacles(1, color1)
        self.assignMultibelObstacles(2, color2)
        self.assignMultibelObstacles(3, color3)
        
    def assignAllObstaclesCustom(self, color4, color2, color3, color1):
        self.assignMultibelObstacles(0, color4)
        self.assignMultibelObstacles(1, color1)
        self.assignMultibelObstacles(2, color2)
        self.assignMultibelObstacles(3, color3)

    def setSpeed(self, speed):
        speed = speed*5.165/30*1000
        self.send("speed,"+str(speed)+"\n")
    
    def setSteer(self, angle):
        # bigger nummer = more left

        # servoTrim = 0.1    # battlecart 1
        servoTrim = 5.5    # battlecart 2
        angle += servoTrim
        self.send("servo,"+str(angle)+"\n")
    
    def setLowVoltageCheck(self, checkVoltage: bool):
        self.send("checkVoltage,"+str(int(checkVoltage))+"\n")

    def send(self, string):
        # print(string)
        b = bytes(string, 'utf-8')
        self.ser.write(b)

    def printValues(self, camValues, cam):
        global lastPrint
        printString = ""
        if time.time() - lastPrint < 0.01:
            return
        subprocess.run("clear", shell=True)
        for i in range(8):
            for j in range(8):
                pos=i*8+j
                val=camValues[cam][pos]
                if val <= 0:
                    printString = "   -" 
                elif val < 10:
                    printString = "   "+str(val)
                elif val < 100:
                    printString = "  "+str(val)
                elif val < 1000:
                    printString = " "+str(val)
                else:
                    printString = str(val)
                print(printString, end=" ")
            print("")
        print(len(camValues[3]))
        lastPrint = time.time()

    def getPosForCam(self, cam, setSensorIndex = False):
        hflip = False
        vflip = False
        rotate = False
        
        # apply transformations to camera and move it to a new positon:
        if cam == 5:            # angle right  -> top right(2)
            vflip = True
            hflip = True
            cam = 2
            if setSensorIndex:
                Parser.angleRightSensor = cam
        elif cam == 1:          # right  -> bottom right(5)
            rotate = True
            vflip = True
            cam = 5
            if setSensorIndex:
                Parser.rightSensor = cam
        elif cam == 2:          # left  -> bottom left(3)
            rotate = True
            hflip = True
            cam = 3
            if setSensorIndex:
                Parser.leftSensor = cam
        elif cam == 3:          # front  -> top middle(1)
            rotate = True
            hflip = True
            cam = 1
            if setSensorIndex:
                Parser.frontSensor = cam
        elif cam == 4:          # angle left -> top left(0)
            vflip = True
            cam = 0
            if setSensorIndex:
                Parser.angleLeftSensor = cam
        elif cam == 0:          # back  -> bottom middle(4)
            rotate = True
            vflip = True
            cam = 4
            if setSensorIndex:
                Parser.backSensor = cam
        
        return cam, hflip, vflip, rotate

    def pars(self):           #(sem)
        

        print("open")


        global lastPrint
        lastPrint = time.time()
        prevCamValues = [[], [], [], [], [], []]

        for i in range(64):                         
            for j in range(self.amountSensors):
                prevCamValues[j].append(0)

        counter=0

        while True:
            try:
                strin = self.ser.readline().decode("utf-8")
                
                # print(strin)

                # inputString = "cam,4,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,\r\n"
                # inputString = self.ser.read(100)


                #inputString = "speed,50,28934,9.01"
                inputString = strin.split(",")




                if inputString[0] == "stat" and len(inputString) == (3 + self.amountSensors):
                    self.voltage = float(inputString[1])
                    for i in range(self.amountSensors):
                        self.sensorCaptures[i] = int(inputString[i+2])
                    
                    # print("Voltage: "+str(self.voltage))

                elif inputString[0] == "speed" and len(inputString) == 6:
                    self.rps = float(inputString[1])
                    self.count = int(inputString[2])
                    self.output = float(inputString[3])
                    self.setpoint = float(inputString[4])
                    self.speed = self.rps/5.165*30/1000
                    self.distance = self.count/5.165

                    # print("Speed:"+str(self.rps)+" Count:"+str(self.count)+" Output:"+str(self.output)+" Setpoint:"+str(self.setpoint))
                
                elif inputString[0] == "cam" and len(inputString) == 67:  
                    # print(inputString)
                    cam = int(inputString[1])-1
                    
                    cam, hflip, vflip, rotate = self.getPosForCam(cam)
                    
                    for j in range(8):              
                        for k in range(8):          
                            if not rotate:
                                x = j
                                y = k
                            else:
                                x = k
                                y = j
                            if hflip:
                                x = 7-x
                            if vflip:
                                y = 7-y
                            
                            pos = x+8*y
                            
                            val=int(inputString[k*8+j+2])
                            
                            if val >= 0:
                                self.camValues[cam][pos] = val
                            else:
                                self.camValues[cam][pos] = 0
                
                elif inputString[0] == "cam" and len(inputString) == 19:  
                    print(inputString)
                    cam = int(inputString[1])-1
                    for j in range(4):              # j flip Vertical | k flip Horizontal
                        for k in range(4):              
                            # if cam == 0:            #back
                            #     pos = (3-j)*4+k      
                            # elif cam == 1:          #right  #5 wall
                            #     pos = (3-j)*4+k
                            # elif cam == 2:          #front  
                            pos = j*4+(3-k)
                            # elif cam == 3:          #left   #5 wall
                            #     pos = j*4+(3-k)
                            
                            val=int(inputString[k*4+j+2])
                            
                            if val >= 0:
                                self.camValues[cam][pos] = val
                            else:
                                self.camValues[cam][pos] = 0                   
                    prevCamValues[cam] = self.camValues[cam].copy()
                elif inputString[0] == "lowVoltage" and len(inputString) == 3:
                    self.voltage = float(inputString[1])
                    self.lowVoltage = True
                    time.sleep(4)

                    call("sudo shutdown -h now", shell=True)
                elif inputString[0] == "button" and len(inputString) == 3:
                    if inputString[1] == "1":
                        self.button = True
                    if self.started:
                        self.sendStartSignal()
                    # print("Button:",self.button)
                    
            except:
                print("\n!!!! Parsing Error !!!!\n")
            
            # ime.sleep(0.01)

    def manualDrive(self):
        maxSpeed = 800
        speed = 0
        angle = 90

        while True:
            Input = input()
            if Input == "w":
                speed += maxSpeed
                if speed > maxSpeed:
                    speed = maxSpeed
                self.send("speed,"+str(speed)+"\n")
            elif Input == "s":
                speed -= maxSpeed
                if speed < -maxSpeed:
                    speed = -maxSpeed
                self.send("speed,"+str(speed)+"\n")
            elif Input == "d":
                angle -= 90
                if angle < 0:
                    angle = 0
                self.send("servo,"+str(angle)+"\n")
            elif Input == "a":
                angle += 90
                if angle > 180:
                    angle = 180
                self.send("servo,"+str(angle)+"\n")
            else:
                self.send("speed,0\n")
                self.send("servo,90\n")
            time.sleep(0.1)

def main():
    parser = Parser()
    parser.pars()

if __name__ == "__main__":
    main()