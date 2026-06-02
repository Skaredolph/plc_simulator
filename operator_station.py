"""
Operator Station — операторская панель управления насосной станцией.

Подключается к MQTT, отображает телеметрию и позволяет отправлять команды.
"""

from __future__ import annotations

import logging
import os
import signal
import sys

from typing import Any

from mqtt.mqtt_client import MqttClient


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
    handlers=[
        logging.FileHandler(
            os.path.join(
                LOGS_DIR,
                "plc.log",
            ),
            encoding="utf-8",
        )
    ],
)

logger = logging.getLogger(
    "operator"
)


# ---------------------------------------------------------------------------
# MQTT топики
# ---------------------------------------------------------------------------
TOPIC_CMD_START = "plant/command/start"
TOPIC_CMD_STOP = "plant/command/stop"
TOPIC_CMD_SET_LEVEL = "plant/command/set_level"

TOPIC_TELEMETRY = "plant/telemetry"
TOPIC_ALARM = "plant/alarm"


# QoS
QOS_COMMANDS = 1
QOS_TELEMETRY = 0
QOS_ALARM = 2


class OperatorStation:

    def __init__(
        self,
        mqtt: MqttClient,
    ) -> None:

        self.mqtt = mqtt

        self.telemetry: dict[
            str,
            Any,
        ] | None = None

        self.alarms: list[
            dict[str, Any]
        ] = []

        self.mqtt.subscribe(
            TOPIC_TELEMETRY,
            self._on_telemetry,
            qos=QOS_TELEMETRY,
        )

        self.mqtt.subscribe(
            TOPIC_ALARM,
            self._on_alarm,
            qos=QOS_ALARM,
        )

    # -------------------------------------------------------------------
    # MQTT callbacks
    # -------------------------------------------------------------------

    def _on_telemetry(
        self,
        _topic: str,
        payload: dict,
    ) -> None:

        self.telemetry = payload

    def _on_alarm(
        self,
        _topic: str,
        payload: dict,
    ) -> None:

        self.alarms.append(
            payload
        )

        print(
            f"\n[ALARM] "
            f"{payload.get('code')} | "
            f"{payload.get('temperature')}°C"
        )

    # -------------------------------------------------------------------
    # MQTT publish
    # -------------------------------------------------------------------

    def _publish(
        self,
        topic: str,
        payload: dict,
    ) -> None:

        self.mqtt.publish(
            topic,
            payload,
            qos=QOS_COMMANDS,
        )

    def send_start(
        self,
    ) -> None:

        self._publish(
            TOPIC_CMD_START,
            {
                "source":
                    "operator"
            },
        )

        print(
            "Pump started"
        )

    def send_stop(
        self,
    ) -> None:

        self._publish(
            TOPIC_CMD_STOP,
            {
                "source":
                    "operator"
            },
        )

        print(
            "Pump stopped"
        )

    def set_level(
        self,
        level: float,
    ) -> None:

        self._publish(
            TOPIC_CMD_SET_LEVEL,
            {
                "value":
                    level
            },
        )

        print(
            f"Level: {level}"
        )

    # -------------------------------------------------------------------
    # Display
    # -------------------------------------------------------------------

    def show_status(
        self,
    ) -> None:

        if not self.telemetry:

            print(
                "No telemetry"
            )

            return

        temp = self.telemetry.get(
            "temperature",
            0,
        )

        indicator = ""

        if temp >= 80:

            indicator = " [CRITICAL]"

        elif temp >= 60:

            indicator = " [WARNING]"

        print("-" * 40)

        print(
            "Pump:",
            "ON"
            if self.telemetry.get(
                "pump_state"
            )
            else "OFF",
        )

        print(
            f"Temp: "
            f"{temp:.1f}°C"
            f"{indicator}"
        )

        print(
            f"Level: "
            f"{self.telemetry.get('water_level', 0):.1f}%"
        )

        print(
            f"Energy: "
            f"{self.telemetry.get('energy', 0):.2f} kWh"
        )

        print("-" * 40)

    def show_alarms(
        self,
    ) -> None:

        if not self.alarms:

            print(
                "No alarms"
            )

            return

        for index, alarm in enumerate(
            self.alarms,
            start=1,
        ):

            print(
                f"{index}. "
                f"{alarm.get('code')} | "
                f"{alarm.get('temperature')}°C"
            )

    @staticmethod
    def show_help() -> None:

        print(
            "\nCommands:\n"
            "  start\n"
            "  stop\n"
            "  set_level <0-100>\n"
            "  status\n"
            "  alarms\n"
            "  help\n"
            "  quit\n"
        )

    # -------------------------------------------------------------------
    # Main loop
    # -------------------------------------------------------------------

    def run(
        self,
    ) -> None:

        commands = {

            "start":
                self.send_start,

            "stop":
                self.send_stop,

            "status":
                self.show_status,

            "alarms":
                self.show_alarms,

            "help":
                self.show_help,
        }

        print("=" * 50)
        print("Operator Station")
        print("=" * 50)

        self.show_help()

        while True:

            try:

                user_input = input(
                    "> "
                ).strip()

            except (
                EOFError,
                KeyboardInterrupt,
            ):

                break

            if not user_input:

                continue

            if user_input in (
                "quit",
                "exit",
            ):

                break

            if user_input.startswith(
                "set_level"
            ):

                parts = user_input.split()

                if len(parts) < 2:

                    print(
                        "Usage: set_level <value>"
                    )

                    continue

                try:

                    self.set_level(
                        float(
                            parts[1]
                        )
                    )

                except ValueError:

                    print(
                        "Invalid level"
                    )

                continue

            action = commands.get(
                user_input.lower()
            )

            if action:

                action()

            else:

                print(
                    "Unknown command"
                )

        print(
            "Exiting..."
        )


def main() -> None:

    logger.info(
        "Operator starting"
    )

    mqtt = MqttClient(
        broker="broker.emqx.io",
        port=1883,
        client_id="operator_station",
    )

    station = OperatorStation(
        mqtt
    )

    def shutdown(
        *_,
    ) -> None:

        logger.info(
            "Shutdown"
        )

        mqtt.disconnect()

        sys.exit(0)

    signal.signal(
        signal.SIGINT,
        shutdown,
    )

    signal.signal(
        signal.SIGTERM,
        shutdown,
    )

    try:

        mqtt.connect()

        station.run()

    finally:

        mqtt.disconnect()


if __name__ == "__main__":

    main()