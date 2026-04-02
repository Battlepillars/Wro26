import serial
import subprocess
import time
import board
import busio
import adafruit_bno055


class Parser:
    def __init__(self):

        self.camValues = [[0 for x in range(64)], [0 for x in range(64)], [0 for x in range(64)], [0 for x in range(64)]]
        self.sensorCaptures = [0,0,0,0]
        self.rps = 0
        self.count = 0
        self.output = 0
        self.setpoint = 0
        self.voltage = 12.6
        self.speed = 0
        self.distance = 0

        i2c = busio.I2C(board.SCL, board.SDA)
        self.gyro = adafruit_bno055.BNO055_I2C(i2c, address=0x28)

        self.ser = serial.Serial()
        self.ser.port = "/dev/ttyAMA0"
        self.ser.baudrate = 921600
        self.ser.bytesize = 8
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.parity = serial.PARITY_NONE
        self.ser.open()


    def setSpeed(self, speed):
        speed = speed*5.165/30*1000
        self.send("speed,"+str(speed)+"\n")
    
    def setSteer(self, angle):
        self.send("servo,"+str(angle)+"\n")

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

    def pars(self):           #(sem)
        

        print("open")


        global lastPrint
        lastPrint = time.time()
        prevCamValues = [[], [], [], []]

        for i in range(64):                         
            for j in range(4):
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


                # sem.acquire()


                if inputString[0] == "stat" and len(inputString) == 7:
                    self.voltage = float(inputString[1])
                    for i in range(4):
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
                    for i in range(len(inputString)-3):
                        val=int(inputString[i+2])
                        if val >= 0:
                            self.camValues[int(inputString[1])-1][i] = val
                        else:
                            self.camValues[int(inputString[1])-1][i] = 0
                            # camValues[int(inputString[1])-1].append(prevCamValues[int(inputString[1])-1][i])

                    #print(str(camValues[int(inputString[1])-1]))
                    # counter+=1
                    # if (counter%30 == 0):
                    #     self.printValues(self.camValues, int(inputString[1])-1)
                    #     print(strin)
                    
                    prevCamValues[int(inputString[1])-1] = self.camValues[int(inputString[1])-1].copy()
            except:
                print("\n!!!! Pars Error !!!!\n")
            
            # sem.release()
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