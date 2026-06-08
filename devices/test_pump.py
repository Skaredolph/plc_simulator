from devices.sensors import TemperatureSensor, WaterLevelSensor, EnergyMeter
from devices.pump import Pump
from devices.states import *


def main():
    temp = TemperatureSensor(25)
    water = WaterLevelSensor(50)
    energy = EnergyMeter(0)

    pump = Pump(temp, water, energy)

    print("=== INITIAL STATE ===")
    print("State:", pump.state_name)
    print("Is running:", pump.is_running)

    print("\n=== START ===")
    pump.start()

    print("State after start:", pump.state_name)
    print("Is running:", pump.is_running)

    print("\n=== UPDATE ===")
    pump.update()

    print("\n=== WATER LEVEL CHANGE ===")
    pump.set_water_level(80)
    print("Water level:", water.value)

    print("\n=== ALARM TEST ===")
    temp._value = 90  # имитация перегрева
    pump.publish_alarm()

    print("\n=== STOP ===")
    pump.stop()

    print("State after stop:", pump.state_name)
    print("Is running:", pump.is_running)



main()