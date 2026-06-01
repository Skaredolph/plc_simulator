"""
Паттерн Factory Method (Фабричный метод)
Создание датчиков через фабрику.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from devices.sensors import EnergyMeter, TemperatureSensor, WaterLevelSensor

logger = logging.getLogger(__name__)


class SensorFactory:
    """Фабрика для создания датчиков.

    Поддерживаемые типы:
        - temperature  -> TemperatureSensor
        - water_level  -> WaterLevelSensor
        - energy       -> EnergyMeter
    """

    @staticmethod
    def create(sensor_type: str, **kwargs):
        """Создать экземпляр датчика указанного типа.

        Args:
            sensor_type: Строковый идентификатор типа датчика.
            **kwargs: Дополнительные аргументы для конструктора датчика.

        Returns:
            Экземпляр соответствующего датчика.

        Raises:
            ValueError: Если указан неизвестный тип датчика.
        """
        from devices.sensors import (
            EnergyMeter,
            TemperatureSensor,
            WaterLevelSensor,
        )

        mapping = {
            "temperature": TemperatureSensor,
            "water_level": WaterLevelSensor,
            "energy": EnergyMeter,
        }

        sensor_class = mapping.get(sensor_type)
        if sensor_class is None:
            available = ", ".join(mapping.keys())
            raise ValueError(
                f"Unknown sensor type: {sensor_type!r}. "
                f"Available types: {available}"
            )

        instance = sensor_class(**kwargs)
        logger.info(
            f"SensorFactory created {sensor_class.__name__} "
            f"for type={sensor_type!r}"
        )
        return instance
