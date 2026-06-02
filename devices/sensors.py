from __future__ import annotations

import logging
from abc import ABC

logger = logging.getLogger(__name__)


class BaseSensor(ABC):

    def __init__(
        self,
        initial_value: float = 0.0,
    ) -> None:

        self._initial_value = initial_value
        self._value = initial_value

    @property
    def value(self) -> float:
        return self._value

    def reset(self) -> None:
        self._value = self._initial_value

        logger.debug(
            "%s reset to %.2f",
            self.__class__.__name__,
            self._value,
        )

    def _change_value(self, delta: float) -> None:
        """Изменить значение датчика."""

        self._value += delta


class TemperatureSensor(BaseSensor):
    def __init__(
        self,
        initial_value: float = 25.0,
    ) -> None:
        super().__init__(initial_value)

        self._cooling_rate = 0.5
        self._heating_rate = 1.0
        self._ambient_temperature = 20.0

    def increase(self) -> None:
        """Нагрев."""
        self._change_value(
            self._heating_rate
        )
        logger.debug(
            "Temperature %.1f°C",
            self._value,
        )

    def cool_down(self) -> None:
        """Естественное охлаждение."""
        self._value = max(
            self._ambient_temperature,
            self._value - self._cooling_rate,
        )
        logger.debug(
            "Temperature %.1f°C",
            self._value,
        )


class WaterLevelSensor(BaseSensor):
    def __init__(
        self,
        initial_value: float = 100.0,
    ) -> None:
        super().__init__(initial_value)
        self._drain_rate = 1.0
        self._min_level = 0.0
        self._max_level = 100.0
        
    def decrease(self) -> None:
        self._value = max(
            self._min_level,
            self._value - self._drain_rate,
        )

        logger.debug(
            "Water level %.1f%%",
            self._value,
        )

    def set_level(
        self,
        level: float,
    ) -> None:

        self._value = max(
            self._min_level,
            min(
                self._max_level,
                level,
            ),
        )

        logger.info(
            "Water level %.1f%%",
            self._value,
        )

class EnergyMeter(BaseSensor):
    def __init__(
        self,
        initial_value: float = 0.0,
    ) -> None:
        super().__init__(initial_value)
        self._accumulation_rate = 0.1

    def accumulate(self) -> None:
        self._change_value(
            self._accumulation_rate
        )
        logger.debug(
            "Energy %.2f kWh",
            self._value,
        )