inputString = "speed,50,28934,9.01,;"
inputString = inputString.split(",")

speed = 0
count = 0
voltage = 0

if inputString[0] == "speed":
    speed = inputString[1]
    count = inputString[2]
    voltage = inputString[3]

print(speed)
print(count)
print(voltage)
