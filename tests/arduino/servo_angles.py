# using pyfirmata to remove dependency on arduino ide
from pyfirmata import Arduino, SERVO
from time import sleep

#board initialization and confirmation print statement
board = Arduino('/dev/cu.usbmodem101')
print("[INFO] Arduino connected, firmware version:", board.firmware)