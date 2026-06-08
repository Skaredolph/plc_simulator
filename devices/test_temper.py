from sensors import *
def main():
    sensor = TemperatureSensor()

    print("Initial temperature:", sensor.value)

    sensor.increase()

    print("After heating:", sensor.value)

    sensor.cool_down()

    print("After cooling:", sensor.value)


if __name__ == "__main__":
    main()