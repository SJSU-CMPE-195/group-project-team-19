import os
import servo_angles as sa
import sys


#home angles
home_angles = {
    "s0": 0,
    "s1": 90,
    "s2": 90,
    "s3": 90,
    "s4": 90,
    "s5": 80,
}

# mapping arduino pins to servos
pin_map = {
    "s0": 13,
    "s1": 12,
    "s2": 11,
    "s3": 10,
    "s4": 9,
    "s5": 8,
}


