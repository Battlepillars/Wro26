import math
import time
import board
import busio
from adafruit_bno08x import _ME_CAL_CONFIG, BNO_REPORT_ROTATION_VECTOR, BNO_REPORT_GAME_ROTATION_VECTOR
from adafruit_bno08x.i2c import BNO08X_I2C



class gyroBNO085:
    """Interface to the BNO085 IMU over I2C using the Adafruit BNO08x library."""

    def __init__(self, address: int = 0x4B, use_magnetometer: bool = False):
        """
        Initialise the sensor.

        address         – I2C address (0x4A default, 0x4B if ADR pin is high)
        use_magnetometer – True  → enable ROTATION_VECTOR (absolute, mag-corrected)
                           False → enable GAME_ROTATION_VECTOR (relative, no mag)
        """
        self._i2c = busio.I2C(board.SCL, board.SDA)
        self._bno = BNO08X_I2C(self._i2c, address=address)
        time.sleep(0.5)  # BNO086 needs time to finish its startup sequence

        self._use_mag = use_magnetometer
        self._heading_offset: float = 0.0

        self._enable_reports()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _enable_reports(self) -> None:
        """Enable the appropriate rotation report on the sensor.

        Retries on 'Unprocessable Batch bytes' which the BNO086 emits during
        its startup flush before settling into normal operation.
        """
        report = BNO_REPORT_ROTATION_VECTOR if self._use_mag else BNO_REPORT_GAME_ROTATION_VECTOR
        for attempt in range(5):
            try:
                self._bno.enable_feature(report)
                return
            except RuntimeError as exc:
                if "Unprocessable Batch bytes" in str(exc) and attempt < 4:
                    time.sleep(0.1)
                    continue
                raise

    @staticmethod
    def _quaternion_to_heading(i: float, j: float, k: float, real: float) -> float:
        """
        Convert a rotation-vector quaternion (i, j, k, real) → heading in degrees.

        The BNO08x quaternion component order is (i, j, k, real) which maps to
        the conventional (x, y, z, w).  Yaw is extracted assuming the sensor's
        Z-axis points up.

        Returns a value in [0, 360).
        """
        x, y, z, w = i, j, k, real
        yaw_rad = math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
        heading = math.degrees(yaw_rad)
        return heading % 360.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_heading(self) -> float:
        """
        Return the current heading in degrees [0, 360), adjusted for any
        zero-offset set by reset_heading().
        """
        if self._use_mag:
            quat = self._bno.quaternion        # (i, j, k, real)
        else:
            quat = self._bno.game_quaternion   # (i, j, k, real)

        if quat is None:
            raise RuntimeError("BNO085: no quaternion data available yet")

        raw = self._quaternion_to_heading(*quat)
        return 360-((raw - self._heading_offset) % 360.0)

    def reset_heading(self) -> None:
        """
        Zero the heading offset so that the current orientation becomes 0°.
        Does NOT reset the sensor hardware.
        """
        if self._use_mag:
            quat = self._bno.quaternion
        else:
            quat = self._bno.game_quaternion

        if quat is None:
            raise RuntimeError("BNO085: no quaternion data available yet")

        self._heading_offset = self._quaternion_to_heading(*quat)

    def reset(self) -> None:
        """
        Soft-reset the sensor and re-enable the rotation report.
        The heading offset accumulated by reset_heading() is also cleared.
        """
        """Begin the sensor's self-calibration routine"""
        # start calibration for accel, gyro, and mag
        self._bno._send_me_command(
            [
                1,  # calibrate accel
                1,  # calibrate gyro
                0,  # calibrate mag
                _ME_CAL_CONFIG,
                0,  # calibrate planar acceleration
                0,  # 'on_table' calibration
                0,  # reserved
                0,  # reserved
                0,  # reserved
            ]
        )
        self._calibration_complete = False



# gyro = gyroBNO085(use_magnetometer=False)  # use GAME_ROTATION_VECTOR for relative heading without magnetometer 
# # gyro.reset()  # start calibration routine#
# while True:
#     try:
#         heading = gyro.get_heading()
#         print(f"Heading: {heading:.2f}°")
#         print(gyro._bno.calibration_status)
#     except RuntimeError as e:
#         print(f"Error reading heading: {e}")
#     time.sleep(0.5)
