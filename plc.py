"""
PLC Simulator — эмулятор программируемого логического контроллера.

Запускает цикл управления насосной станцией и публикует телеметрию.
"""
from __future__ import annotations

import json
import logging
import os
import signal
import sys
import threading
import time
from typing import Any

from devices.pump import Pump
from devices.sensors import EnergyMeter, TemperatureSensor, WaterLevelSensor
from models.telemetry import AlarmData, TelemetryData
from mqtt.mqtt_client import MqttClient
from patterns.factory import SensorFactory
from patterns.observer import Observer

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
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("plc")

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


class AlarmManager(Observer):
    """Менеджер аварий — подписчик на события насоса.

    Получает уведомления через паттерн Observer и публикует alarm в MQTT.
    """

    def __init__(self, mqtt_client: MqttClient) -> None:
        self.mqtt_client = mqtt_client

    def update(self, event_type: str, data: dict[str, Any]) -> None:
        if event_type == "alarm":
            alarm = AlarmData(
                code=data.get("code", "UNKNOWN"),
                temperature=data.get("temperature", 0.0),
            )
            self.mqtt_client.publish(
                TOPIC_ALARM,
                json.loads(alarm.to_json()),
                qos=QOS_ALARM,
                retain=False,
            )
            logger.critical(f"Alarm published: {alarm.to_json()}")

        elif event_type == "pump_state_changed":
            logger.info(
                f"Pump state changed: {data.get('old_state')} -> {data.get('new_state')}"
            )


class PlcController:
    """Контроллер ПЛК — основной класс управления станцией."""

    def __init__(self, mqtt_client: MqttClient) -> None:
        self.mqtt = mqtt_client
        self._running = False
        self._telemetry_thread: threading.Thread | None = None

        # Создаём датчики через Factory Method
        self._temp_sensor = SensorFactory.create("temperature", initial_value=25.0)
        self._level_sensor = SensorFactory.create("water_level", initial_value=100.0)
        self._energy_meter = SensorFactory.create("energy", initial_value=0.0)

        # Создаём насос с датчиками
        self.pump = Pump(
            temperature_sensor=self._temp_sensor,
            water_level_sensor=self._level_sensor,
            energy_meter=self._energy_meter,
        )

        # Подключаем AlarmManager как Observer
        self._alarm_manager = AlarmManager(self.mqtt)
        self.pump.subscribe(self._alarm_manager)

        # Регистрируем обработчики MQTT-команд
        self._register_mqtt_handlers()

    def _register_mqtt_handlers(self) -> None:
        """Подписаться на команды от оператора."""
        self.mqtt.subscribe(TOPIC_CMD_START, self._on_cmd_start, qos=QOS_COMMANDS)
        self.mqtt.subscribe(TOPIC_CMD_STOP, self._on_cmd_stop, qos=QOS_COMMANDS)
        self.mqtt.subscribe(TOPIC_CMD_SET_LEVEL, self._on_cmd_set_level, qos=QOS_COMMANDS)

    def _on_cmd_start(self, topic: str, payload: dict) -> None:
        """Обработать команду запуска."""
        source = payload.get("source", "unknown")
        logger.info(f"Received START command from {source}")
        self.pump.start()

    def _on_cmd_stop(self, topic: str, payload: dict) -> None:
        """Обработать команду остановки."""
        source = payload.get("source", "unknown")
        logger.info(f"Received STOP command from {source}")
        self.pump.stop()

    def _on_cmd_set_level(self, topic: str, payload: dict) -> None:
        """Обработать команду установки уровня воды."""
        value = payload.get("value", 0)
        logger.info(f"Received SET_LEVEL command: {value}")
        self.pump.set_water_level(value)

    def _telemetry_loop(self) -> None:
        """Цикл публикации телеметрии (1 Гц)."""
        logger.info("Telemetry loop started")
        while self._running:
            try:
                # Обновляем логику насоса
                self.pump.update()

                # Формируем телеметрию
                telemetry = TelemetryData(
                    pump_state=self.pump.is_running,
                    temperature=self._temp_sensor.value,
                    water_level=self._level_sensor.value,
                    energy=self._energy_meter.value,
                )

                # Публикуем с retain=True
                self.mqtt.publish(
                    TOPIC_TELEMETRY,
                    json.loads(telemetry.to_json()),
                    qos=QOS_TELEMETRY,
                    retain=True,
                )

                logger.debug(f"Telemetry published: {telemetry.to_json()}")
            except Exception as exc:
                logger.error(f"Error in telemetry loop: {exc}", exc_info=True)

            time.sleep(1.0)

        logger.info("Telemetry loop stopped")

    def start(self) -> None:
        """Запустить ПЛК."""
        logger.info("Starting PLC controller...")
        self._running = True

        self._telemetry_thread = threading.Thread(
            target=self._telemetry_loop,
            name="TelemetryThread",
            daemon=True,
        )
        self._telemetry_thread.start()

        logger.info("PLC controller is running")

    def stop(self) -> None:
        """Остановить ПЛК."""
        logger.info("Stopping PLC controller...")
        self._running = False

        if self._telemetry_thread is not None:
            self._telemetry_thread.join(timeout=2.0)

        # Очищаем retained сообщение
        self.mqtt.publish(TOPIC_TELEMETRY, "", qos=QOS_TELEMETRY, retain=True)
        logger.info("PLC controller stopped")


# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------
def main() -> None:
    logger.info("=" * 60)
    logger.info("PLC Simulator starting")
    logger.info("Broker: broker.emqx.io:1883")
    logger.info("=" * 60)

    mqtt_client = MqttClient(
        broker="broker.emqx.io",
        port=1883,
        client_id="plc_simulator_main",
    )

    plc = PlcController(mqtt_client)

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        plc.stop()
        mqtt_client.disconnect()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        mqtt_client.connect()
        plc.start()

        # Основной поток ждёт сигнала завершения
        while True:
            time.sleep(1)
    except Exception as exc:
        logger.critical(f"Fatal error: {exc}", exc_info=True)
        plc.stop()
        mqtt_client.disconnect()
        sys.exit(1)


if __name__ == "__main__":
    main()
