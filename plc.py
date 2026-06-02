"""
PLC Simulator — эмулятор программируемого логического контроллера.

Запускает цикл управления насосной станцией и публикует телеметрию.
"""

from __future__ import annotations

import logging
import os
import signal
import sys
import threading
import time

from dataclasses import asdict
from typing import Any

from devices.pump import Pump
from models.telemetry import AlarmData, TelemetryData
from mqtt.mqtt_client import MqttClient
from patterns.factory import SensorFactory
from patterns.observer import Observer


# ---------------------------------------------------------------------------
# Логирование
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

LOGS_DIR = os.path.join(
    SCRIPT_DIR,
    "logs",
)

os.makedirs(
    LOGS_DIR,
    exist_ok=True,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(
                LOGS_DIR,
                "plc.log",
            ),
            encoding="utf-8",
        ),
        logging.StreamHandler(
            sys.stdout
        ),
    ],
)

logger = logging.getLogger(
    "plc"
)


# ---------------------------------------------------------------------------
# MQTT топики
# ---------------------------------------------------------------------------

TOPIC_CMD_START = "plant/command/start"
TOPIC_CMD_STOP = "plant/command/stop"
TOPIC_CMD_SET_LEVEL = "plant/command/set_level"

TOPIC_TELEMETRY = "plant/telemetry"
TOPIC_ALARM = "plant/alarm"


QOS_COMMANDS = 1
QOS_TELEMETRY = 0
QOS_ALARM = 2


class AlarmManager(
    Observer
):

    def __init__(
        self,
        mqtt: MqttClient,
    ):

        self.mqtt = mqtt

    def update(
        self,
        event_type: str,
        data: dict[str, Any],
    ) -> None:

        if event_type == "alarm":

            alarm = AlarmData.from_dict(
                data
            )

            self.mqtt.publish(
                TOPIC_ALARM,
                asdict(
                    alarm
                ),
                qos=QOS_ALARM,
                retain=False,
            )

            logger.critical(
                "Alarm published: %s",
                alarm,
            )

        elif event_type == "pump_state_changed":

            logger.info(
                "Pump state %s -> %s",
                data.get(
                    "old_state"
                ),
                data.get(
                    "new_state"
                ),
            )


class PlcController:

    def __init__(
        self,
        mqtt: MqttClient,
    ):

        self.mqtt = mqtt

        self._running = False

        self._thread: threading.Thread | None = None

        self.temp_sensor = SensorFactory.create(
            "temperature",
            initial_value=25,
        )

        self.level_sensor = SensorFactory.create(
            "water_level",
            initial_value=100,
        )

        self.energy_meter = SensorFactory.create(
            "energy",
            initial_value=0,
        )

        self.pump = Pump(
            temperature_sensor=self.temp_sensor,
            water_level_sensor=self.level_sensor,
            energy_meter=self.energy_meter,
        )

        self.pump.subscribe(
            AlarmManager(
                self.mqtt
            )
        )

        self._register_handlers()

    def _register_handlers(
        self,
    ):

        self.mqtt.subscribe(
            TOPIC_CMD_START,
            self._on_start,
            qos=QOS_COMMANDS,
        )

        self.mqtt.subscribe(
            TOPIC_CMD_STOP,
            self._on_stop,
            qos=QOS_COMMANDS,
        )

        self.mqtt.subscribe(
            TOPIC_CMD_SET_LEVEL,
            self._on_set_level,
            qos=QOS_COMMANDS,
        )

    def _on_start(
        self,
        _topic,
        payload,
    ):

        logger.info(
            "START %s",
            payload.get(
                "source"
            )
        )

        self.pump.start()

    def _on_stop(
        self,
        _topic,
        payload,
    ):

        logger.info(
            "STOP %s",
            payload.get(
                "source"
            )
        )

        self.pump.stop()

    def _on_set_level(
        self,
        _topic,
        payload,
    ):

        level = payload.get(
            "value",
            0,
        )

        logger.info(
            "SET LEVEL %s",
            level,
        )

        self.pump.set_water_level(
            level
        )

    def _telemetry_loop(
        self,
    ):

        logger.info(
            "Telemetry started"
        )

        while self._running:

            try:

                self.pump.update()

                telemetry = TelemetryData(

                    pump_state=
                    self.pump.is_running,

                    temperature=
                    self.temp_sensor.value,

                    water_level=
                    self.level_sensor.value,

                    energy=
                    self.energy_meter.value,
                )

                self.mqtt.publish(
                    TOPIC_TELEMETRY,
                    asdict(
                        telemetry
                    ),
                    qos=QOS_TELEMETRY,
                    retain=True,
                )

            except Exception:

                logger.exception(
                    "Telemetry error"
                )

            time.sleep(
                1
            )

    def start(
        self,
    ):

        self._running = True

        self._thread = threading.Thread(
            target=self._telemetry_loop,
            daemon=True,
        )

        self._thread.start()

        logger.info(
            "PLC started"
        )

    def stop(
        self,
    ):

        self._running = False

        if self._thread:

            self._thread.join(
                timeout=2
            )

        self.mqtt.publish(
            TOPIC_TELEMETRY,
            "",
            qos=QOS_TELEMETRY,
            retain=True,
        )

        logger.info(
            "PLC stopped"
        )


def main():

    mqtt = MqttClient(
        broker="broker.emqx.io",
        port=1883,
        client_id="plc_simulator",
    )

    plc = PlcController(
        mqtt
    )

    def shutdown(
        *_,
    ):

        plc.stop()

        mqtt.disconnect()

        sys.exit(
            0
        )

    signal.signal(
        signal.SIGINT,
        shutdown,
    )

    signal.signal(
        signal.SIGTERM,
        shutdown,
    )

    mqtt.connect()

    plc.start()

    try:

        while True:

            time.sleep(
                1
            )

    finally:

        plc.stop()

        mqtt.disconnect()


if __name__ == "__main__":

    main()