"""
Паттерн State (Состояние)
Реализация состояний для Pump.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from devices.pump import Pump

logger = logging.getLogger(__name__)


class PumpState(ABC):
    """Абстрактное состояние насоса."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Возвращает строковое имя состояния."""
        ...

    @abstractmethod
    def start(self, pump: Pump) -> None:
        """Обработать команду запуска.

        Args:
            pump: Ссылка на контекст-насос.
        """
        ...

    @abstractmethod
    def stop(self, pump: Pump) -> None:
        """Обработать команду остановки.

        Args:
            pump: Ссылка на контекст-насос.
        """
        ...

    @abstractmethod
    def update(self, pump: Pump) -> None:
        """Выполнить логику обновления каждый цикл.

        Args:
            pump: Ссылка на контекст-насос.
        """
        ...


class StoppedState(PumpState):
    """Состояние 'Остановлен'."""

    @property
    def name(self) -> str:
        return "STOPPED"

    def start(self, pump: Pump) -> None:
        if pump.alarm_active:
            logger.warning("Cannot start pump: alarm is active")
            return
        pump.transition_to(RunningState())
        logger.info("Pump started from StoppedState")

    def stop(self, pump: Pump) -> None:
        logger.debug("Pump is already stopped")

    def update(self, pump: Pump) -> None:
        # Когда насос выключен — температура плавно снижается
        pump.temperature_sensor.cool_down()


class RunningState(PumpState):
    """Состояние 'Работает'."""

    @property
    def name(self) -> str:
        return "RUNNING"

    def start(self, pump: Pump) -> None:
        logger.debug("Pump is already running")

    def stop(self, pump: Pump) -> None:
        pump.transition_to(StoppedState())
        logger.info("Pump stopped from RunningState")

    def update(self, pump: Pump) -> None:
        # Когда насос включен — каждую секунду:
        pump.temperature_sensor.increase()
        pump.energy_meter.accumulate()
        pump.water_level_sensor.decrease()

        if pump.temperature_sensor.value > pump.overheat_threshold:
            logger.critical(
                f"Overheat detected: {pump.temperature_sensor.value}°C"
            )
            pump.transition_to(AlarmState())
            pump._publish_alarm()


class AlarmState(PumpState):
    """Состояние 'Авария' (перегрев)."""

    @property
    def name(self) -> str:
        return "ALARM"

    def start(self, pump: Pump) -> None:
        logger.error("Cannot start pump: alarm state is active (overheat)")

    def stop(self, pump: Pump) -> None:
        pump.transition_to(StoppedState())
        pump.alarm_active = False
        logger.info("Alarm reset and pump stopped")

    def update(self, pump: Pump) -> None:
        # В аварийном состоянии насос не работает — температура снижается
        pump.temperature_sensor.cool_down()
