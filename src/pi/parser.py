import serial # type: ignore
import subprocess
import time
import math
import board # type: ignore
import busio # type: ignore
import adafruit_bno055 # type: ignore
from glob import glob
from subprocess import call
from gyro85 import gyroBNO085


class Parser:
    """@brief Shared data model and serial bridge between CM5 and STM32.

    Holds the latest sensor readings (ToF grids, speed, heading, voltage),
    runs the serial read loop in `pars()`, exposes helpers to send drive
    commands to the STM32, and tracks the detected obstacle layout.
    """
    RED = 0
    GREEN = 1
    
    amountSensors = 6
    leftSensor = 0      # 0
    frontSensor = 1     
    rightSensor = 2
    backSensor = 3
    angleRightSensor = 4
    angleLeftSensor = 5
    CW = 0
    CCW = 1
    Default = 0
    Capture_1_Only = 1
    Capture_Dynamic = 2
    All = 0
    HSV = 1
    
    def __init__(self):
        """@brief Initialize shared state, the gyro and the serial port.

        Sets up the per-sensor ToF buffers, waits for gyro calibration and
        opens the UART to the STM32 at 921600 baud.
        @return None
        """
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
        self.uiType = Parser.Default
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
        
        self.imageType = Parser.All
        self.currentImage = 0
        self.images = sorted(glob("capture/*.jpg"))         # get all files in captureStore ending with .jpg
        self.hsvImages = sorted(glob("capture/*hsv.jpg"))   # get all files in captureStore ending with hsv.jpg

    def loadImages(self):
        """@brief Refresh the cached lists of captured images for the UI viewer.

        @return None
        """
        self.images = sorted(glob("capture/*.jpg"))         # get all files in captureStore ending with .jpg
        self.hsvImages = sorted(glob("capture/*hsv.jpg"))   # get all files in captureStore ending with hsv.jpg

    def calibDone(self):
        """@brief Report whether the gyro reports a usable calibration state.

        @return bool True when calibration is complete (currently always True).
        """
        return True
        # _, gyroCalibration, _, magnetometerCalibration = self.gyro.calibration_status
        # return gyroCalibration == 3

    def getHeading(self):
        """@brief Return the current heading in degrees from the BNO085 gyro.

        Applies a small per-lap correction offset that compensates for the
        gyro drifting slightly more to one side depending on drive direction.
        @return float heading angle in degrees.
        """
        # return self.gyro85.get_heading()
    
        # if not hasattr(self, 'gyro') or self.gyro is None:
        #     return 0
        
        # angle = self.gyro.euler[0]
        angle = self.gyro85.get_heading()
        
        if angle is None:
            angle = 0
        
        # Per-lap drift compensation: the gyro accumulates a small bias each
        # lap, so nudge the heading a little further every round.
        if self.Direction == self.CCW:
            if self.round == 0:
                angle += 0
            elif self.round == 1:
                angle += -1
            elif self.round == 2:
                angle += -1.5                     # kleinere Zahl (mehr negativ)  = er steuer mehr nach rechts
        else:
            if self.round == 0:
                angle += 0
            elif self.round == 1:
                angle += 1
            elif self.round == 2:
                angle += 2
        
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
        """@brief Zero the gyro heading so the current orientation becomes 0°.

        @return None
        """
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
        """@brief Tell the STM32 the CM5 is initialized and ready to start.

        @return None
        """
        self.send("ready,1\n")

    def sendStartSignal(self):
        """@brief Tell the STM32 the run has started (e.g. button pressed).

        @return None
        """
        self.send("start,1\n")

    def checkSection(self, section, mirror = False):
        """@brief Return the first detected obstacle color in a course section.

        @param section int section index 0..3 (each holds 3 obstacle slots).
        @param mirror  bool when True, swap sections 1 and 3 (direction mirror).
        @return the obstacle color (RED/GREEN) or None if the section is empty.
        """
        if mirror:
            if section == 1:
                section = 3
            elif section == 3:
                section = 1
        
        for i in range(3):
            if self.obstacles[i+section*3] != None:
                return self.obstacles[i+section*3]
        return None
    
    def checkSectionAuto(self, section):
        """@brief Return a section's obstacle color, mirrored for the drive direction.

        Scans the section's slots in forward or reverse order depending on
        the current direction and returns the color as seen from the car.
        @param section int section index 0..3.
        @return the (direction-adjusted) obstacle color or None.
        """
        mirror = False
        if self.Direction == self.CW:
            mirror = True
            if section == 1:
                section = 3
            elif section == 3:
                section = 1
        
        # Scan slots in reverse order when mirrored so the first obstacle the
        # car actually reaches is returned first.
        rangeArgs = (2,-1,-1) if mirror else (0,3,1)
        
        for i in range(*rangeArgs):
            if self.obstacles[i+section*3] != None:
                return self.oppositeColor(self.obstacles[i + section*3], mirror)
        return None
    
    def checkSectionMulti(self, section, mirror=False, colorMirror=False):
        """@brief Return the ordered list of obstacle colors in a section.

        Guarantees at least two entries: an empty section defaults to GREEN,
        and a single obstacle is duplicated so callers can always index [0]/[1].
        @param section     int section index 0..3.
        @param mirror      bool swap sections 1/3 and reverse slot order.
        @param colorMirror bool invert each returned color (RED<->GREEN).
        @return list of obstacle colors with length >= 2.
        """
        if mirror:
            if section == 1:
                section = 3
            elif section == 3:
                section = 1

        rangeArgs = (2,-1,-1) if mirror else (0,3,1)
        
        obstacleList = [
            self.oppositeColor(self.obstacles[i + section*3], colorMirror)
            for i in range(*rangeArgs)
            if self.obstacles[i+section*3] is not None
        ]
        if len(obstacleList) == 0:
            obstacleList.append(self.GREEN)
            print("!!! No obstacles in section " + str(section) + "!!!")
        if len(obstacleList) == 1:
            obstacleList.append(obstacleList[0])   # duplicate so [0] and [1] are always valid
        return obstacleList
    
    def oppositeColor(self, color, condtion=True):
        """@brief Optionally invert an obstacle color.

        @param color    the obstacle color (RED/GREEN/None).
        @param condtion bool when True invert the color, otherwise return it unchanged.
        @return the (possibly inverted) color.
        """
        if condtion:
            if color == self.RED:
                return self.GREEN
            if color == self.GREEN:
                return self.RED
            return None
        else:
            return color

    def colorName(self, color):
        """@brief Convert an obstacle color constant into a readable string.

        @param color the obstacle color (RED/GREEN/None).
        @return str "RED", "GREEN", "NONE" or the raw value as string.
        """
        if color == self.RED:
            return "RED"
        if color == self.GREEN:
            return "GREEN"
        if color is None:
            return "NONE"
        return str(color)

    def assignMultibelObstacles(self, section, obstacleType, obstacles = [0,1,2]):
        """@brief Assign the same color to every slot of one section.

        @param section      int section index 0..3.
        @param obstacleType  color to store in each slot of the section.
        @param obstacles     iterable whose length sets how many slots to fill.
        @return None
        """
        for i in range(len(obstacles)):
            self.obstacles[i+section*3] = obstacleType

    def assignAllObstacles(self, colors: tuple):
        """@brief Store a full-course scan result into the obstacle layout.

        Accepts the 4 (or 5) section colors returned by a scan routine and
        writes them into `obstacles[0..11]`.
        @param colors tuple of 4 section colors, or 5 when section 0 has a
                      distinct left obstacle.
        @return None
        """
        color4Left = None
        if len(colors) == 4:
            color1, color2, color3, color4 = colors
        else: 
            color1, color2, color3, color4, color4Left = colors
        
        # Section 0 holds either a right obstacle (slot 0) or, if there is none,
        # a left obstacle (slot 2) – never both.
        if color4 is not None:
            self.obstacles[0] = color4
        else:
            self.obstacles[2] = color4Left
        self.assignMultibelObstacles(1, color1)
        self.assignMultibelObstacles(2, color2)
        self.assignMultibelObstacles(3, color3)
        
    def assignAllObstaclesCustom(self, color4, color2, color3, color1):
        """@brief Store a hand-picked obstacle layout (used for testing).

        @param color4 color for section 0.
        @param color2 color for section 2.
        @param color3 color for section 3.
        @param color1 color for section 1.
        @return None
        """
        self.assignMultibelObstacles(0, color4)
        self.assignMultibelObstacles(1, color1)
        self.assignMultibelObstacles(2, color2)
        self.assignMultibelObstacles(3, color3)

    def setSpeed(self, speed):
        """@brief Send a target drive speed to the STM32.

        Converts m/s into the STM32's internal encoder-counts/cycle unit
        (v[m/s] = count * 30 / (5.165 * 1000)).
        @param speed float target speed in m/s.
        @return None
        """
        speed = speed*5.165/30*1000
        self.send("speed,"+str(speed)+"\n")
    
    def setSteer(self, angle):
        """@brief Send a steering angle to the STM32, applying the servo trim.

        @param angle float steering angle: 0 = full right, 90 = straight,
                     180 = full left (higher number = more left).
        @return None
        """
        # bigger nummer = more left

        # servoTrim = 0.1    # car 1
        servoTrim = 5.5    # car 2
        angle += servoTrim
        self.send("servo,"+str(angle)+"\n")
        
    def setTowerAngle(self, angle):
        """@brief Aim the camera tower servo by converting an angle to a pulse width.

        Maps 0..270° onto the servo's usable pulse-width range and sends it to
        the STM32.
        @param angle float tower angle in degrees (0..270).
        @return None
        """
        servoTrim = 0
        angle += servoTrim
        
        pulseWidthMin = 550     # ab 545 dreht er sich wild   # 400 min theoretically
        pulseWidthMax = 2600
        angleMin = 0
        angleMax = 270
        # Linear angle->pulse map, clamped so an out-of-range angle can never
        # drive the servo past its safe mechanical limits.
        pulseWidth = min(pulseWidthMax, max(pulseWidthMin, (pulseWidthMax-pulseWidthMin) * (angle-angleMin) / (angleMax-angleMin) + pulseWidthMin))
        
        self.send("servo_tower,"+str(pulseWidth)+"\n")  # 400-2600 / 0-270
    
    def setLowVoltageCheck(self, checkVoltage: bool):
        """@brief Enable or disable the STM32's low-battery auto-shutdown check.

        @param checkVoltage bool True to enable the voltage guard.
        @return None
        """
        self.send("checkVoltage,"+str(int(checkVoltage))+"\n")

    def send(self, string):
        """@brief Write a raw command string to the STM32 over UART.

        @param string str command terminated by a newline.
        @return None
        """
        # print(string)
        b = bytes(string, 'utf-8')
        self.ser.write(b)

    def printValues(self, camValues, cam):
        """@brief Print one ToF sensor's 8x8 distance grid to the console.

        Rate-limited and mainly used for debugging sensor output.
        @param camValues list of per-sensor distance grids.
        @param cam       int sensor index to print.
        @return None
        """
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
        """@brief Map a physical sensor id to its UI grid slot and orientation.

        Each VL53L8CX is mounted at a different angle, so this returns the
        flips/rotation needed to display its 8x8 grid consistently and, when
        requested, records which grid slot each named sensor lives in.
        @param cam           int physical sensor id.
        @param setSensorIndex bool when True, store the resolved slot into the
                             matching Parser.*Sensor class attribute.
        @return tuple (cam, hflip, vflip, rotate) – remapped slot and transforms.
        """
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
        elif cam == 2:          # left  -> bottom left(3)      #2
            rotate = True
            hflip = True
            cam = 3
            if setSensorIndex:
                Parser.leftSensor = cam
        elif cam == 3:          # front  -> top middle(1)       #3
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
        """@brief Serial read loop that continuously parses STM32 status packets.

        Runs in its own thread. Decodes "stat", "speed", "cam", "lowVoltage"
        and "button" messages and updates the shared fields used by the rest
        of the program. Triggers shutdown on a low-voltage message.
        @return None (loops forever)
        """
        

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
                    # Convert raw encoder counts into real-world units (5.165
                    # counts per mm, empirically calibrated).
                    self.speed = self.rps/5.165*30/1000
                    self.distance = self.count/5.165

                    # print("Speed:"+str(self.rps)+" Count:"+str(self.count)+" Output:"+str(self.output)+" Setpoint:"+str(self.setpoint))
                
                elif inputString[0] == "cam" and len(inputString) == 67:  
                    # print(inputString)
                    cam = int(inputString[1])-1
                    
                    cam, hflip, vflip, rotate = self.getPosForCam(cam)
                    
                    # Re-orient each sensor's 8x8 grid into a common frame so all
                    # sensors share the same up/left convention before storing.
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
                                self.camValues[cam][pos] = 0   # -1 (invalid) -> 0
                
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
                    time.sleep(4)   # let the UI show the warning before powering off

                    call("sudo shutdown -h now", shell=True)
                elif inputString[0] == "button" and len(inputString) == 3:
                    if inputString[1] == "1":
                        self.button = True
                    if self.started:
                        self.sendStartSignal()   # re-arm the STM32 if the run is already active
                    # print("Button:",self.button)
                    
            except:
                print("\n!!!! Parsing Error !!!!\n")   # ignore malformed/partial serial lines
            
            # ime.sleep(0.01)

    def manualDrive(self):
        """@brief Simple keyboard REPL to drive the car manually (w/a/s/d).

        Reads single characters from stdin and sends matching speed/steering
        commands; any other key stops and centers the car.
        @return None (loops forever)
        """
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
    """@brief Standalone entry point: open the parser and run its read loop.

    @return None
    """
    parser = Parser()
    parser.pars()

if __name__ == "__main__":
    main()