import json

from telemetry import TelemetryData, AlarmData


def test_telemetry_to_json():
    telemetry = TelemetryData(
        pump_state=True,
        temperature=25.5,
        water_level=80.0,
        energy=123.4,
    )

    result = telemetry.to_json()

    print("\nTelemetry JSON:")
    print(result)

    parsed = json.loads(result)

    assert parsed == {
        "pump_state": True,
        "temperature": 25.5,
        "water_level": 80.0,
        "energy": 123.4,
    }


def test_alarm_to_json():
    alarm = AlarmData(
        code="OVERHEAT",
        temperature=95.0,
    )

    result = alarm.to_json()

    print("\nAlarm JSON:")
    print(result)

    parsed = json.loads(result)

    assert parsed == {
        "code": "OVERHEAT",
        "temperature": 95.0,
    }


def test_telemetry_from_dict():
    data = {
        "pump_state": True,
        "temperature": 22.1,
        "water_level": 50.0,
        "energy": 10.5,
    }

    telemetry = TelemetryData.from_dict(data)

    print("\nTelemetry object:")
    print(telemetry)

    assert telemetry.pump_state is True
    assert telemetry.temperature == 22.1
    assert telemetry.water_level == 50.0
    assert telemetry.energy == 10.5


def test_alarm_from_dict():
    data = {
        "code": "HIGH_TEMP",
        "temperature": 88.8,
    }

    alarm = AlarmData.from_dict(data)

    print("\nAlarm object:")
    print(alarm)

    assert alarm.code == "HIGH_TEMP"
    assert alarm.temperature == 88.8


def test_extra_fields_are_ignored():
    data = {
        "pump_state": True,
        "temperature": 20,
        "water_level": 10,
        "energy": 5,
        "unexpected": "ignored",
    }

    telemetry = TelemetryData.from_dict(data)

    print("\nIgnored extra fields:")
    print(telemetry)

    assert not hasattr(telemetry, "unexpected")


def test_defaults():
    telemetry = TelemetryData()
    alarm = AlarmData()

    print("\nDefault telemetry:")
    print(telemetry)

    print("\nDefault alarm:")
    print(alarm)

    assert telemetry == TelemetryData()
    assert alarm == AlarmData()
    
    
test_alarm_from_dict()

test_alarm_to_json()

test_defaults()

test_extra_fields_are_ignored()

test_telemetry_from_dict()

test_telemetry_to_json()
