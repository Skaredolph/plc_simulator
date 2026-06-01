"""
Модели данных для телеметрии и аварий.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass


@dataclass
class TelemetryData:
    """Модель телеметрических данных насосной станции."""

    pump_state: bool
    temperature: float
    water_level: float
    energy: float

    def to_json(self) -> str:
        """Сериализовать в JSON-строку.

        Returns:
            JSON-строка с данными телеметрии.
        """
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> TelemetryData:
        """Создать экземпляр из словаря.

        Args:
            data: Словарь с полями телеметрии.

        Returns:
            Экземпляр TelemetryData.
        """
        return cls(
            pump_state=data.get("pump_state", False),
            temperature=data.get("temperature", 0.0),
            water_level=data.get("water_level", 0.0),
            energy=data.get("energy", 0.0),
        )


@dataclass
class AlarmData:
    """Модель данных аварийного сообщения."""

    code: str
    temperature: float

    def to_json(self) -> str:
        """Сериализовать в JSON-строку.

        Returns:
            JSON-строка с данными аварии.
        """
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> AlarmData:
        """Создать экземпляр из словаря.

        Args:
            data: Словарь с полями аварии.

        Returns:
            Экземпляр AlarmData.
        """
        return cls(
            code=data.get("code", "UNKNOWN"),
            temperature=data.get("temperature", 0.0),
        )
