from sensors import *


def main():
    sensor = WaterLevelSensor()

    print("Initial level:", sensor.value)

    sensor.decrease()

    print("After decrease:", sensor.value)

    sensor.set_level(75)

    print("Set level 75:", sensor.value)

    sensor.set_level(200)

    print("Set level 200 (clamped):", sensor.value)

    sensor.set_level(-50)

    print("Set level -50 (clamped):", sensor.value)


if __name__ == "__main__":
    main()