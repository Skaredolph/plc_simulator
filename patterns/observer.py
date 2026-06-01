"""
Паттерн Observer (Наблюдатель)
Собственная система событий для уведомления подписчиков.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class Observer(ABC):
    """Абстрактный наблюдатель."""

    @abstractmethod
    def update(self, event_type: str, data: dict[str, Any]) -> None:
        """Вызывается при получении уведомления от Subject.

        Args:
            event_type: Тип произошедшего события.
            data: Данные, связанные с событием.
        """
        ...


class Subject(ABC):
    """Абстрактный субъект наблюдения."""

    def __init__(self) -> None:
        self._observers: list[Observer] = []

    def subscribe(self, observer: Observer) -> None:
        """Подписать наблюдателя на уведомления.

        Args:
            observer: Экземпляр наблюдателя.
        """
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug(f"Observer {observer.__class__.__name__} subscribed to {self.__class__.__name__}")

    def unsubscribe(self, observer: Observer) -> None:
        """Отписать наблюдателя от уведомлений.

        Args:
            observer: Экземпляр наблюдателя.
        """
        if observer in self._observers:
            self._observers.remove(observer)
            logger.debug(f"Observer {observer.__class__.__name__} unsubscribed from {self.__class__.__name__}")

    def notify(self, event_type: str, data: dict[str, Any]) -> None:
        """Уведомить всех подписанных наблюдателей.

        Args:
            event_type: Тип события.
            data: Данные события.
        """
        logger.debug(
            f"Subject {self.__class__.__name__} notifying {len(self._observers)} "
            f"observer(s) about event: {event_type}"
        )
        for observer in self._observers:
            try:
                observer.update(event_type, data)
            except Exception as exc:
                logger.error(
                    f"Error notifying observer {observer.__class__.__name__}: {exc}",
                    exc_info=True,
                )
