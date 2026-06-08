from enum import Enum, auto
import logging
from devices.sensors import (
EnergyMeter,
TemperatureSensor,
WaterLevelSensor,
)

logger = logging.getLogger(__name__)


class SensorType(Enum):
    TEMPERATURE = auto()
    WATER_LEVEL = auto()
    ENERGY = auto()

    @classmethod
    def from_string(cls, value: str):
        try:
            return cls[value.upper()]
        
        except KeyError:
            available = ", ".join(x.name.lower() for x in cls)
            raise ValueError(
                f"Unknown sensor type: {value!r}. "
                f"Available types: {available}"
            )


class SensorFactory:

    @classmethod
    def _get_sensor_class(cls, sensor_type):

        mapping = {
            SensorType.TEMPERATURE: TemperatureSensor,
            SensorType.WATER_LEVEL: WaterLevelSensor,
            SensorType.ENERGY: EnergyMeter,
        }

        return mapping[sensor_type]

    @classmethod
    def create(cls, sensor_type: str | SensorType, **kwargs):

        if isinstance(sensor_type, str):
            sensor_type = SensorType.from_string(sensor_type)

        sensor_class = cls._get_sensor_class(sensor_type)

        logger.info(
            "Created %s for %s",
            sensor_class.__name__,
            sensor_type.name,
        )

        return sensor_class(**kwargs)