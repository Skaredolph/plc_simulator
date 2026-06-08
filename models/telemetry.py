"""
Модели данных для телеметрии и аварий.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass


@dataclass
class BaseModel:
    """Базовая модель данных."""

    def to_json(self) -> str:
        """Сериализовать модель в JSON."""

        return json.dumps(
            asdict(self),
            indent=2,
        )

    @classmethod
    def from_dict(
        cls,
        data: dict,
    ):
        """Создать объект из словаря."""

        field_names = cls.__dataclass_fields__

        filtered = {
            key: value
            for key, value in data.items()
            if key in field_names
        }

        return cls(**filtered)

@dataclass
class TelemetryData(BaseModel):
    """Телеметрические данные насосной станции."""

    pump_state: bool = False
    temperature: float = 0.0
    water_level: float = 0.0
    energy: float = 0.0
    
@dataclass
class AlarmData(BaseModel):
    """Данные аварии."""

    code: str = "UNKNOWN"
    temperature: float = 0.0