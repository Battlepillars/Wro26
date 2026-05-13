import time
import os
import sys
import select
import termios
import tty
import board
import busio
import adafruit_bno055

i2c = busio.I2C(board.SCL, board.SDA)
bno = adafruit_bno055.BNO055_I2C(i2c, address=0x28)
stdin_fd = sys.stdin.fileno()
old_terminal_settings = termios.tcgetattr(stdin_fd)


def read_keypress():
    if select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.read(1).lower()
    return None
bno.mode = adafruit_bno055.IMUPLUS_MODE
try:
    tty.setcbreak(stdin_fd)

    while True:
        os.system("clear||cls")

        print("Press p to print offsets")
        print("Temp:", bno.temperature)
        print("Euler:", bno.euler)          # heading, roll, pitch
        print("Gyro:", bno.gyro)            # rad/s
        print("Accel:", bno.acceleration)   # m/s^2
        print("Mag:", bno.magnetic)         # uT
        print("Quat:", bno.quaternion)
        print("Calibration:", bno.calibration_status)
        print("       sys gyro accel mag")
        print("---")

        if read_keypress() == "r":
            del bno
            bno = adafruit_bno055.BNO055_I2C(i2c, address=0x28)
            bno.mode = adafruit_bno055.IMUPLUS_MODE


        if read_keypress() == "p":
            print(f"Offsets_Magnetometer:  {bno.offsets_magnetometer}")
            print(f"Offsets_Gyroscope:     {bno.offsets_gyroscope}")
            print(f"Offsets_Accelerometer: {bno.offsets_acceleprometer}")
            time.sleep(5)

        time.sleep(0.4)
finally:
    termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_terminal_settings)