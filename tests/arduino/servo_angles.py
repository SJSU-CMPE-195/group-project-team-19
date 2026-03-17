# using pyfirmata to remove dependency on arduino ide
from pyfirmata import Arduino, SERVO
from time import sleep

#board initialization and confirmation print statement
board = Arduino('/dev/cu.usbmodem101')
print("[INFO] Arduino connected, firmware version:", board.firmware)


def get_servo_angle() -> int:
    """Recieve an angle from the user to be used for the servo."""
    print("Input angle")
    return int(input())
