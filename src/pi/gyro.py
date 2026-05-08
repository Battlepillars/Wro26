import time
import os
import board
import busio
import adafruit_bno055

i2c = busio.I2C(board.SCL, board.SDA)
bno = adafruit_bno055.BNO055_I2C(i2c, address=0x28)

while True:
    os.system("clear||cls")
    
    print("Temp:", bno.temperature)
    print("Euler:", bno.euler)          # heading, roll, pitch
    print("Gyro:", bno.gyro)            # rad/s
    print("Accel:", bno.acceleration)   # m/s^2
    print("Mag:", bno.magnetic)         # uT
    print("Quat:", bno.quaternion)
    print("Calibration:", bno.calibration_status)
    print("---")
    time.sleep(0.4)