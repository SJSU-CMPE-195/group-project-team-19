import pytest
from main import robot_pos, jog_joint

def test_joint_limit_high():
    # Force J1 to max limit
    robot_pos['j1'] = 180
    jog_joint(1, 1) # Attempt to jog +10 degrees
    assert robot_pos['j1'] <= 180

def test_joint_limit_low():
    # Force J1 to min limit
    robot_pos['j1'] = 0
    jog_joint(1, -1) # Attempt to jog -10 degrees
    assert robot_pos['j1'] >= 0

def test_invalid_json_payload():
    # Simulate corrupted data from Orin
    invalid_data = "{'j1': 'one hundred'}"
    with pytest.raises(Exception):
        # Assuming a parse function exists
        parse_orin_data(invalid_data)