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

    name: str

    @abstractmethod
    def start(
        self,
        pump: Pump,
    ) -> None:
        ...

    @abstractmethod
    def stop(
        self,
        pump: Pump,
    ) -> None:
        ...

    @abstractmethod
    def update(
        self,
        pump: Pump,
    ) -> None:
        ...


class StoppedState(PumpState):

    name = "STOPPED"

    def start(
        self,
        pump: Pump,
    ) -> None:

        if pump.state_name == "ALARM":

            logger.warning(
                "Cannot start: alarm active"
            )

            return

        pump.transition_to(
            RunningState()
        )

    def stop(
        self,
        pump: Pump,
    ) -> None:

        pass

    def update(
        self,
        pump: Pump,
    ) -> None:

        pump.temperature_sensor.cool_down()


class RunningState(PumpState):

    name = "RUNNING"

    def start(
        self,
        pump: Pump,
    ) -> None:

        pass

    def stop(
        self,
        pump: Pump,
    ) -> None:

        pump.transition_to(
            StoppedState()
        )

    def update(
        self,
        pump: Pump,
    ) -> None:

        pump.temperature_sensor.increase()

        pump.energy_meter.accumulate()

        pump.water_level_sensor.decrease()

        if (
            pump.temperature_sensor.value
            >
            pump.overheat_threshold
        ):

            logger.critical(
                "Overheat %.1f°C",
                pump.temperature_sensor.value,
            )

            pump.transition_to(
                AlarmState()
            )

            pump.publish_alarm()


class AlarmState(PumpState):

    name = "ALARM"

    def start(
        self,
        pump: Pump,
    ) -> None:

        logger.error(
            "Cannot start while alarm active"
        )

    def stop(
        self,
        pump: Pump,
    ) -> None:

        pump.transition_to(
            StoppedState()
        )

    def update(
        self,
        pump: Pump,
    ) -> None:

        pump.temperature_sensor.cool_down()