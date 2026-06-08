from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from devices.states import StoppedState

from patterns.observer import Subject

if TYPE_CHECKING:
    from devices.sensors import (
        EnergyMeter,
        TemperatureSensor,
        WaterLevelSensor,
    )

    from devices.states import PumpState


logger = logging.getLogger(__name__)


class Pump(Subject):

    def __init__(
        self,
        temperature_sensor: TemperatureSensor,
        water_level_sensor: WaterLevelSensor,
        energy_meter: EnergyMeter,
    ) -> None:

        super().__init__()

        self.temperature_sensor = temperature_sensor
        self.water_level_sensor = water_level_sensor
        self.energy_meter = energy_meter

        self.overheat_threshold = 80.0

        

        self._state: PumpState = StoppedState()

        logger.info(
            "Pump initialized: %s",
            self._state.name,
        )

    @property
    def state_name(self) -> str:

        return self._state.name

    @property
    def is_running(self) -> bool:

        return self.state_name == "RUNNING"

    def transition_to(
        self,
        state: PumpState,
    ) -> None:

        old_state = self._state.name

        self._state = state

        logger.info(
            "State %s -> %s",
            old_state,
            state.name,
        )

        self.notify(
            event_type="pump_state_changed",
            data={
                "old_state": old_state,
                "new_state": state.name,
            },
        )

    def start(self) -> None:

        self._state.start(self)

    def stop(self) -> None:

        self._state.stop(self)

    def update(self) -> None:

        self._state.update(self)

    def publish_alarm(self) -> None:

        self.notify(
            event_type="alarm",
            data={
                "code": "OVERHEAT",
                "temperature":
                    self.temperature_sensor.value,
            },
        )

        logger.critical(
            "OVERHEAT %.1f°C",
            self.temperature_sensor.value,
        )

    def set_water_level(
        self,
        level: float,
    ) -> None:

        self.water_level_sensor.set_level(level)