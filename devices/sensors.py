"""
Реализация датчиков насосной станции.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseSensor(ABC):
    """Базовый класс для всех датчиков."""

    def __init__(self, name: str, initial_value: float = 0.0) -> None:
        self.name = name
        self._value = initial_value

    @property
    def value(self) -> float:
        """Текущее значение датчика."""
        return self._value

    @abstractmethod
    def update(self) -> None:
        """Обновить значение датчика."""
        ...

    def reset(self) -> None:
        """Сбросить значение в начальное."""
        self._value = 0.0
        logger.debug(f"Sensor {self.name} reset to 0")


class TemperatureSensor(BaseSensor):
    """Датчик температуры двигателя."""

    def __init__(self, initial_value: float = 25.0) -> None:
        super().__init__(name="TemperatureSensor", initial_value=initial_value)
        self._cooling_rate = 0.5  # Скорость охлаждения, °C/сек
        self._heating_rate = 1.0   # Скорость нагрева, °C/сек

    def increase(self) -> None:
        """Увеличить температуру (нагрев)."""
        self._value += self._heating_rate
        logger.debug(f"Temperature increased to {self._value:.1f}°C")

    def cool_down(self) -> None:
        """Уменьшить температуру (естественное охлаждение)."""
        if self._value > 20.0:
            self._value = max(20.0, self._value - self._cooling_rate)
            logger.debug(f"Temperature cooled to {self._value:.1f}°C")

    def update(self) -> None:
        """Обновление выполняется через increase/cool_down."""
        pass


class WaterLevelSensor(BaseSensor):
    """Датчик уровня воды (в процентах)."""

    def __init__(self, initial_value: float = 100.0) -> None:
        super().__init__(name="WaterLevelSensor", initial_value=initial_value)
        self._drain_rate = 1.0    # Скорость убывания уровня, %/сек
        self._min_level = 0.0
        self._max_level = 100.0

    def decrease(self) -> None:
        """Уменьшить уровень воды."""
        if self._value > self._min_level:
            self._value = max(self._min_level, self._value - self._drain_rate)
            logger.debug(f"Water level decreased to {self._value:.1f}%")

    def set_level(self, level: float) -> None:
        """Установить уровень воды.

        Args:
            level: Новое значение уровня (0-100).
        """
        self._value = max(self._min_level, min(self._max_level, level))
        logger.info(f"Water level set to {self._value:.1f}%")

    def update(self) -> None:
        """Обновление выполняется через decrease/set_level."""
        pass


class EnergyMeter(BaseSensor):
    """Счетчик электроэнергии (кВт·ч)."""

    def __init__(self, initial_value: float = 0.0) -> None:
        super().__init__(name="EnergyMeter", initial_value=initial_value)
        self._accumulation_rate = 0.1  # кВт·ч/сек

    def accumulate(self) -> None:
        """Накопить энергию."""
        self._value += self._accumulation_rate
        logger.debug(f"Energy accumulated to {self._value:.2f} kWh")

    def update(self) -> None:
        """Обновление выполняется через accumulate."""
        pass
