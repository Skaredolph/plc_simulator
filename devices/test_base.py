from sensors import BaseSensor


class DummySensor(BaseSensor):
    pass


def main():
    sensor = DummySensor(10)

    print("Initial:", sensor.value)

    sensor._change_value(5)

    print("After change:", sensor.value)

    sensor.reset()

    print("After reset:", sensor.value)


if __name__ == "__main__":
    main()