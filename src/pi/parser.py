import serial
import subprocess
import time


ser = serial.Serial()
ser.port = "COM3"
ser.baudrate = 921600
ser.bytesize = 8
ser.stopbits = serial.STOPBITS_ONE
ser.parity = serial.PARITY_NONE

ser.open()

print("open")

global lastPrint
lastPrint = time.time()
prevCamValues = [[], [], [], []]

for i in range(64):                         
    for j in range(4):
        prevCamValues[j].append(0)


def printValues():
    global lastPrint
    printString = ""
    if time.time() - lastPrint < 0.01:
        return
    subprocess.run("cls", shell=True)
    cam=int(inputString[1])-1
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

counter=0

while True:
    strin = ser.readline().decode("utf-8")
    # print(inputString)

    # inputString="cam,4,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,\r\n"
    #inputString = ser.read(100)


    #inputString = "speed,50,28934,9.01"
    inputString = strin.split(",")



    speed = 0
    count = 0
    voltage = 0

    camValues = [[], [], [], []]     # Kamera größe: 8*8


    if inputString[0] == "speed" and len(inputString) == 5 and 1==2:
        speed = inputString[1]
        count = inputString[2]
        voltage = inputString[3]

        print("Speed:"+speed+" Count:"+count+" Voltage:"+voltage)
    
    elif inputString[0] == "cam" and len(inputString) == 67:  
        
        for i in range(len(inputString)-3):
            val=int(inputString[i+2])
            if val >= 0:
                camValues[int(inputString[1])-1].append(val)
            else:
                camValues[int(inputString[1])-1].append(0)
                # camValues[int(inputString[1])-1].append(prevCamValues[int(inputString[1])-1][i])

        #print(str(camValues[int(inputString[1])-1]))
        counter+=1
        if (counter%30 == 0):
            printValues()
            print(strin)
        
        prevCamValues[int(inputString[1])-1] = camValues[int(inputString[1])-1].copy()
    
    # ime.sleep(0.01)

