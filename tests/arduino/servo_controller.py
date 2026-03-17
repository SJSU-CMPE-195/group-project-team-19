import os
import servo_angles as sa
import sys


# default behaviour, can be toggled via command-line argument or environment
# use: `DEBUG=1 python servo_controller.py`
debug_mode = True
if "--no-debug" in sys.argv or os.environ.get("DEBUG","1").startswith("0"):
    debug_mode = False
elif "--debug" in sys.argv or os.environ.get("DEBUG","0").startswith("1"):
    debug_mode = True

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


# dictionary for ServoChannel objects
# each entry holds pin and angle
servos: dict[str, sa.ServoChannel] = {}
for name, pin in pin_map.items():
    initial_angle = home_angles.get(name)
    servos[name] = sa.ServoChannel(pin, initial_angle)


def set_speed(name: str, speed: float) -> None:
    """Set the movement speed for servo."""
    servos[name].speed = speed


def get_speed(name: str) -> float:
    """Return current speedfor servo."""
    return servos[name].speed

def prompt_all_angles() -> None:
    #input angle for each servo
    print("Enter angles for each servo (0-180). Leave blank to keep current value.")
    for name, servo in servos.items():
        current = servo.current_angle if servo.current_angle is not None else 0
        raw = input(f"{name} (pin {servo.pin_number}) [current={current}]: ")
        if raw.strip():
            try:
                angle = int(raw)
                if 0 <= angle <= 180:
                    servo.set_angle(angle)
                else:
                    print("  angle out of range, ignoring")
            except ValueError:
                print("  invalid integer, ignoring")
	
