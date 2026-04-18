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
	

if __name__ == "__main__":
    # show initial state
    print("servo_controller starting (debug_mode=", debug_mode, ")")
    for name, servo in servos.items():
        print(f"{name}: pin {servo.pin_number}, angle {servo.current_angle}")

    if debug_mode:
        print("[DEBUG] entering per-servo command loop (Ctrl-C to exit)")
        while True:
            try:
                num_raw = input(f"servo # (0-{len(servos)-1}): ")
            except KeyboardInterrupt:
                print("\nexiting debug mode")
                break
            if not num_raw.strip():
                continue
            try:
                num = int(num_raw)
            except ValueError:
                print("  please enter a valid integer")
                continue
            if not (0 <= num < len(servos)):
                print("  servo number out of range")
                continue

            try:
                angle_raw = input(f"angle for s{num} (0-180): ")
            except KeyboardInterrupt:
                print("\nexiting debug mode")
                break
            if not angle_raw.strip():
                continue
            try:
                angle = int(angle_raw)
            except ValueError:
                print("  please enter a valid integer")
                continue
            if not (0 <= angle <= 180):
                print("  angle out of range")
                continue

            servo_name = f"s{num}"
            servos[servo_name].set_angle(angle)
            print(f"Set {servo_name} to {angle} degrees")
    else:
        # normal mode
        prompt_all_angles()
        print("updated angles:")
        for name, servo in servos.items():
            print(f"{name}: {servo.current_angle}")
