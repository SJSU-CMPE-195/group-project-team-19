import servo_controller as sc
import time


def main():
    print("Integration Test")
    #servo test existence and home position
    test_setup()
    #servo test movement one at a time
    test_single()

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
