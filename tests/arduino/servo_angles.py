# using pyfirmata to remove dependency on arduino ide
from pyfirmata import Arduino, SERVO
from time import sleep

#board initialization and confirmation print statement
board = Arduino('/dev/cu.usbmodem101')
print("[INFO] Arduino connected, firmware version:", board.firmware)


#servo class for attributtes and functions
class ServoChannel:
    """Single servo attached to the Arduino.
    Attributes:
        pin_number (int): the digital pin used for PWM.
        pin: the pyfirmata pin object.
        current_angle (int | None): last angle written, or ``None`` if unset.
        speed (float): seconds per degree when stepping; lower is faster.
    """


    def __init__(self, pin: int, initial_angle: int | None = None, *, speed: float = 0.02):
        self.pin_number = pin
        self.pin = board.digital[pin]
        self.pin.mode = SERVO
        self.current_angle = None
        # seconds per degree movement; user may adjust later
        self.speed = speed
        if initial_angle is not None:
            self.set_angle(initial_angle)
    
    def set_angle(self, angle: int) -> None:
        self.pin.write(angle)
        self.current_angle = angle
            
    def step_to(self, angle: int, step: int = 1, delay: float | None = None) -> None:
        start = self.current_angle if self.current_angle is not None else 0
        if start == angle:
            return
        if delay is None:
            delay = self.speed * step
        direction = 1 if angle >= start else -1
        for a in range(start, angle + direction, direction * step):
            self.set_angle(a)
            sleep(delay)
        if a != angle:
            self.set_angle(angle)
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
def get_servo_angle() -> int:
    """Recieve an angle from the user to be used for the servo."""
    print("Input angle")
    return int(input())
