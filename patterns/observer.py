"""
Паттерн Observer (Наблюдатель)
Собственная система событий.
"""

from __future__ import annotations

import logging

from abc import (
    ABC,
    abstractmethod,
)

from typing import Any


logger = logging.getLogger(
    __name__
)


class Observer(ABC):

    @abstractmethod
    def update(
        self,
        event_type: str,
        data: dict[str, Any],
    ) -> None:
        ...


class Subject:

    def __init__(
        self,
    ) -> None:

        self._observers: list[
            Observer
        ] = []

    def subscribe(
        self,
        observer: Observer,
    ) -> None:

        if observer not in self._observers:

            self._observers.append(
                observer
            )

            logger.debug(
                "%s subscribed",
                observer.__class__.__name__,
            )

    def unsubscribe(
        self,
        observer: Observer,
    ) -> None:

        try:

            self._observers.remove(
                observer
            )

        except ValueError:

            pass

    def notify(
        self,
        event_type: str,
        data: dict[str, Any],
    ) -> None:

        logger.debug(
            "Notify %d observers (%s)",
            len(
                self._observers
            ),
            event_type,
        )

        for observer in self._observers.copy():

            try:

                observer.update(
                    event_type,
                    data,
                )

            except Exception:

                logger.exception(
                    "Observer failed: %s",
                    observer.__class__.__name__,
                )