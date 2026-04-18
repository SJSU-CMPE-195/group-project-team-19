import unittest
from unittest.mock import patch
import servo_controller as sc


class FakeServo:
    def __init__(self, pin_number=0, current_angle=90, speed=0.02):
        self.pin_number = pin_number
        self.current_angle = current_angle
        self.speed = speed

    def set_angle(self, angle):
        self.current_angle = angle
        
class TestServoController(unittest.TestCase):
    def setUp(self):
        self.fake_servos = {
            "s0": FakeServo(pin_number=13, current_angle=0),
            "s1": FakeServo(pin_number=12, current_angle=90),
            "s2": FakeServo(pin_number=11, current_angle=90),
            "s3": FakeServo(pin_number=10, current_angle=90),
            "s4": FakeServo(pin_number=9, current_angle=90),
            "s5": FakeServo(pin_number=8, current_angle=80),
        }

        patcher = patch.dict(sc.servos, self.fake_servos, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        
    def test_set_speed_updates_selected_servo(self):
        sc.set_speed("s2", 0.05)
        self.assertEqual(sc.servos["s2"].speed, 0.05)

    def test_get_speed_returns_current_speed(self):
        sc.servos["s4"].speed = 0.03
        self.assertEqual(sc.get_speed("s4"), 0.03)
        
    
    def test_set_speed_only_changes_one_servo(self):
        original_s1 = sc.servos["s1"].speed
        original_s3 = sc.servos["s3"].speed

        sc.set_speed("s2", 0.08)

        self.assertEqual(sc.servos["s2"].speed, 0.08)
        self.assertEqual(sc.servos["s1"].speed, original_s1)
        self.assertEqual(sc.servos["s3"].speed, original_s3)
        
    def test_home_angles_match_expected_starting_values(self):
        self.assertEqual(sc.servos["s0"].current_angle, 0)
        self.assertEqual(sc.servos["s1"].current_angle, 90)
        self.assertEqual(sc.servos["s2"].current_angle, 90)
        self.assertEqual(sc.servos["s3"].current_angle, 90)
        self.assertEqual(sc.servos["s4"].current_angle, 90)
        self.assertEqual(sc.servos["s5"].current_angle, 80)

    def test_invalid_servo_name_raises_keyerror(self):
        with self.assertRaises(KeyError):
            sc.set_speed("s9", 0.05)

    def test_get_speed_invalid_servo_name_raises_keyerror(self):
        with self.assertRaises(KeyError):
            sc.get_speed("s9")
            
if __name__ == "__main__":
    unittest.main()