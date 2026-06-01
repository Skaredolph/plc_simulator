"""
Реализация насоса с использованием паттерна State.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from patterns.observer import Subject

if TYPE_CHECKING:
    from devices.sensors import EnergyMeter, TemperatureSensor, WaterLevelSensor
    from devices.states import PumpState

logger = logging.getLogger(__name__)


class Pump(Subject):
    """Насос — контекст для паттерна State.

    Управляет состоянием, датчиками и публикацией аварий.
    """

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
        self.alarm_active = False

        from devices.states import StoppedState
        self._state: PumpState = StoppedState()
        logger.info(f"Pump initialized in state: {self._state.name}")

    @property
    def state_name(self) -> str:
        """Возвращает текущее состояние насоса."""
        return self._state.name

    @property
    def is_running(self) -> bool:
        """True если насос в состоянии RUNNING."""
        return self._state.name == "RUNNING"

    def transition_to(self, state: PumpState) -> None:
        """Перейти в новое состояние.

        Args:
            state: Новое состояние насоса.
        """
        old_name = self._state.name
        self._state = state
        logger.info(f"Pump state transition: {old_name} -> {state.name}")

        if state.name == "ALARM":
            self.alarm_active = True

        # Уведомляем наблюдателей о смене состояния
        self.notify(
            event_type="pump_state_changed",
            data={
                "old_state": old_name,
                "new_state": state.name,
            },
        )

    def start(self) -> None:
        """Команда запуска насоса."""
        logger.debug("Pump.start() called")
        self._state.start(self)

    def stop(self) -> None:
        """Команда остановки насоса."""
        logger.debug("Pump.stop() called")
        self._state.stop(self)

    def update(self) -> None:
        """Обновить логику насоса (вызывается каждый цикл)."""
        self._state.update(self)

    def _publish_alarm(self) -> None:
        """Опубликовать сообщение об аварии через Observer."""
        alarm_data = {
            "code": "OVERHEAT",
            "temperature": self.temperature_sensor.value,
        }
        logger.critical(f"ALARM published: {alarm_data}")
        self.notify(event_type="alarm", data=alarm_data)

    def set_water_level(self, level: float) -> None:
        """Установить уровень воды.

        Args:
            level: Новый уровень воды (0-100).
        """
        self.water_level_sensor.set_level(level)
        logger.info(f"Water level externally set to {level}")
