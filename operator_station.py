"""
Operator Station — операторская панель управления насосной станцией.

Подключается к MQTT, отображает телеметрию и позволяет отправлять команды.
"""
from __future__ import annotations

import json
import logging
import os
import signal
import sys
import time
from typing import Any

from mqtt.mqtt_client import MqttClient

# ---------------------------------------------------------------------------
# Настройка логирования
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(SCRIPT_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOGS_DIR, "plc.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("operator")

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
    """Операторская станция."""

    def __init__(self, mqtt_client: MqttClient) -> None:
        self.mqtt = mqtt_client
        self._running = False
        self._last_telemetry: dict[str, Any] | None = None
        self._alarm_history: list[dict[str, Any]] = []

        self._register_mqtt_handlers()

    def _register_mqtt_handlers(self) -> None:
        """Подписаться на телеметрию и аварии."""
        self.mqtt.subscribe(TOPIC_TELEMETRY, self._on_telemetry, qos=QOS_TELEMETRY)
        self.mqtt.subscribe(TOPIC_ALARM, self._on_alarm, qos=QOS_ALARM)

    def _on_telemetry(self, topic: str, payload: dict) -> None:
        """Обработать сообщение телеметрии."""
        self._last_telemetry = payload

    def _on_alarm(self, topic: str, payload: dict) -> None:
        """Обработать аварийное сообщение."""
        self._alarm_history.append(payload)
        print(f"\n[ALARM] Code: {payload.get('code')} | Temp: {payload.get('temperature')}°C")
        print("> ", end="", flush=True)

    def send_start(self) -> None:
        """Отправить команду запуска насоса."""
        self.mqtt.publish(
            TOPIC_CMD_START,
            {"source": "operator"},
            qos=QOS_COMMANDS,
        )
        print("Pump started")

    def send_stop(self) -> None:
        """Отправить команду остановки насоса."""
        self.mqtt.publish(
            TOPIC_CMD_STOP,
            {"source": "operator"},
            qos=QOS_COMMANDS,
        )
        print("Pump stopped")

    def send_set_level(self, level: float) -> None:
        """Отправить команду установки уровня воды.

        Args:
            level: Новый уровень воды (0-100).
        """
        self.mqtt.publish(
            TOPIC_CMD_SET_LEVEL,
            {"value": level},
            qos=QOS_COMMANDS,
        )
        print(f"Level changed to {level}")

    def display_telemetry(self) -> None:
        """Вывести текущую телеметрию на экран."""
        if self._last_telemetry is None:
            print("No telemetry data yet...")
            return

        state_icon = "ON" if self._last_telemetry.get("pump_state") else "OFF"
        temp = self._last_telemetry.get("temperature", 0.0)
        level = self._last_telemetry.get("water_level", 0.0)
        energy = self._last_telemetry.get("energy", 0.0)

        # Цветовая индикация температуры
        temp_indicator = ""
        if temp >= 80:
            temp_indicator = " [CRITICAL]"
        elif temp >= 60:
            temp_indicator = " [WARNING]"

        print("-" * 40)
        print(f"  Pump:    {state_icon}")
        print(f"  Temp:    {temp:.1f}°C{temp_indicator}")
        print(f"  Level:   {level:.1f}%")
        print(f"  Energy:  {energy:.2f} kWh")
        print("-" * 40)

    def display_alarms(self) -> None:
        """Вывести историю аварий."""
        if not self._alarm_history:
            print("No alarms recorded")
            return

        print("Alarm History:")
        for idx, alarm in enumerate(self._alarm_history, 1):
            print(f"  {idx}. Code: {alarm.get('code')} | Temp: {alarm.get('temperature')}°C")

    def display_help(self) -> None:
        """Вывести справку по командам."""
        print("Available commands:")
        print("  start              - Start the pump")
        print("  stop               - Stop the pump")
        print("  set_level <value>  - Set water level (0-100)")
        print("  status             - Show current telemetry")
        print("  alarms             - Show alarm history")
        print("  help               - Show this help message")
        print("  quit / exit        - Exit the operator station")

    def run(self) -> None:
        """Запустить интерактивный цикл операторской станции."""
        self._running = True
        print("=" * 50)
        print("  Operator Station")
        print("  Connected to broker.emqx.io:1883")
        print("=" * 50)
        print()
        self.display_help()
        print()

        while self._running:
            try:
                user_input = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nShutting down...")
                break

            if not user_input:
                continue

            parts = user_input.split()
            command = parts[0].lower()

            if command == "start":
                self.send_start()
            elif command == "stop":
                self.send_stop()
            elif command == "set_level":
                if len(parts) < 2:
                    print("Usage: set_level <value>")
                    continue
                try:
                    level = float(parts[1])
                    self.send_set_level(level)
                except ValueError:
                    print("Invalid level value. Must be a number.")
            elif command == "status":
                self.display_telemetry()
            elif command == "alarms":
                self.display_alarms()
            elif command == "help":
                self.display_help()
            elif command in ("quit", "exit"):
                print("Exiting...")
                break
            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands")

        self._running = False


def main() -> None:
    logger.info("Operator Station starting")

    mqtt_client = MqttClient(
        broker="broker.emqx.io",
        port=1883,
        client_id="operator_station_main",
    )

    station = OperatorStation(mqtt_client)

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        mqtt_client.disconnect()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        mqtt_client.connect()
        station.run()
    except Exception as exc:
        logger.critical(f"Fatal error: {exc}", exc_info=True)
    finally:
        mqtt_client.disconnect()


if __name__ == "__main__":
    main()
