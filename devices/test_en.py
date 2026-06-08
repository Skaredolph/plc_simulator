from sensors import *


def main():
    meter = EnergyMeter()

    print("Initial energy:", meter.value)

    for _ in range(5):
        meter.accumulate()

    print("After accumulation:", meter.value)

    meter.reset()

    print("After reset:", meter.value)


if __name__ == "__main__":
    main()