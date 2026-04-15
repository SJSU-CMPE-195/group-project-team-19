import servo_controller as sc

def main():
    print("Integration Test")
    #servo test
    test_setup()

if __name__ == "__main__":
    main()

def test_setup():
        print("Testing setup for servos")

        for name in sc.servos:
            #verify home position and that it is recongnized
            print(name, sc.servos[name].current_angle)