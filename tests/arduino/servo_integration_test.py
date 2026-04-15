import servo_controller as sc
import time


def main():
    print("Integration Test")
    #servo test existence and home position
    test_setup()
    #servo test movement one at a time
    test_single()
    #multiple servo test
    test_sequence()
    #servo speed test
    test_speed()

    #invalid angle
    test_invalid_angle()

if __name__ == "__main__":
    main()

def test_setup():
        print("Testing setup for servos")

        for name in sc.servos:
            #verify home position and that it is recongnized
            print(name, sc.servos[name].current_angle)

#testing servo movement
def test_single():
    print("Testing 1 servo at a time")

    ok = True

    for i in range(6):
        #servo starting from bottom s0-s5
        name = "s" + str(i)
        #test angle
        angle = 45

        #send command through controller 
        sc.servos[name].set_angle(angle)
        time.sleep(0.3)

        #print updated angle, after movement
        #print(name, "->", sc.servos[name].current_angle)

        #adding pass fail for maintability and testing
        if sc.servos[name].current_angle == angle:
            #print the servo name and pass/fail
            print(name, "passed")
        else:
            print(name, "failed")
            ok = False

    return ok

#multiple servo test
def test_sequence():
    print("Testing multiple servos at a time")

    for i in range(6):
        name = "s" + str(i)
        #move to home position in contoller.py
        angle = sc.home_angles[name]
        sc.servos[name].set_angle(angle)

        time.sleep(0.3)

#servo speed test
def test_speed():
    print("Testing servo speed")

    #replace sX with servo testing
    name = "s2"

    # slowest to fastest
    speeds = [0.01, 0.02, 0.03, 0.04, 0.05]

    for s in speeds:
        sc.set_speed(name, s)

        print("Speed set to:", s)

        sc.servos[name].set_angle(30)
        time.sleep(0.5)

        sc.servos[name].set_angle(90)


joint_limits = {
    "s0": (20, 160),
    "s1": (30, 140),
    "s2": (40, 150),
    "s3": (30, 150),
    "s4": (0, 180),
    "s5": (40, 120)
}

#invalid angles for each joint
test_invalid_angle():
    print("Testing invalid angle for each joint")
    
    ok = True

    for i in range(6):
        name = "s" + str(i)

        min_a, max_a = joint_limits[name] 

        #test above and below limits
        test_angle = [min_a - 10, max_a + 10]

        for angle in test_angle:
            try:
                sc.servos[name].set_angle(angle)

                #if error isnt output, test failed
                print(name, "failed for angle:", angle)
                ok = False

            except:
                #expected output
                print(name, "passed for angle:", angle)
    return ok