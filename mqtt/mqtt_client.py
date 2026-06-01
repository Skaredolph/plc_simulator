"""
MQTT клиент — обёртка над paho-mqtt.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any, Callable

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MqttClient:
    """Клиент для подключения к MQTT брокеру.

    Поддерживает публикацию/подписку, QoS, retained messages.
    """

    def __init__(
        self,
        broker: str = "broker.emqx.io",
        port: int = 1883,
        client_id: str | None = None,
    ) -> None:
        self.broker = broker
        self.port = port
        self._client_id = client_id or f"plc_sim_{int(time.time())}"
        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
            client_id=self._client_id,
        )
        self._callbacks: dict[str, Callable[[str, dict], None]] = {}
        self._lock = threading.Lock()
        self._connected = False

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: dict,
        rc: int,
        properties=None,
    ) -> None:
        """Callback при подключении к брокеру."""
        if rc == 0:
            self._connected = True
            logger.info(f"Connected to MQTT broker {self.broker}:{self.port}")

            # Переподписываемся на все ранее добавленные топики
            with self._lock:
                for topic in self._callbacks.keys():
                    self._client.subscribe(topic)
                    logger.debug(f"Re-subscribed to {topic}")
        else:
            logger.error(f"MQTT connection failed with code {rc}")

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        rc: int,
    ) -> None:
        """Callback при отключении от брокера."""
        self._connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection (rc={rc})")

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: Any,
        msg: mqtt.MQTTMessage,
    ) -> None:
        """Callback при получении сообщения."""
        topic = msg.topic
        try:
            payload_str = msg.payload.decode("utf-8")
            payload = json.loads(payload_str)
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = {"raw": msg.payload.decode("utf-8", errors="replace")}

        logger.debug(f"Received on {topic}: {payload}")

        with self._lock:
            callback = self._callbacks.get(topic)

        if callback:
            try:
                callback(topic, payload)
            except Exception as exc:
                logger.error(f"Error in callback for {topic}: {exc}", exc_info=True)

    def connect(self) -> None:
        """Подключиться к MQTT брокеру."""
        logger.info(f"Connecting to {self.broker}:{self.port}...")
        self._client.connect(self.broker, self.port, keepalive=60)
        self._client.loop_start()

        # Ждём установления соединения
        attempts = 0
        while not self._connected and attempts < 30:
            time.sleep(0.1)
            attempts += 1

        if not self._connected:
            raise ConnectionError("Failed to connect to MQTT broker")

    def disconnect(self) -> None:
        """Отключиться от брокера."""
        self._client.loop_stop()
        self._client.disconnect()
        self._connected = False
        logger.info("Disconnected from MQTT broker")

    def subscribe(
        self,
        topic: str,
        callback: Callable[[str, dict], None],
        qos: int = 1,
    ) -> None:
        """Подписаться на топик.

        Args:
            topic: MQTT топик.
            callback: Функция-обработчик (topic, payload).
            qos: Уровень QoS.
        """
        with self._lock:
            self._callbacks[topic] = callback

        if self._connected:
            self._client.subscribe(topic, qos=qos)
            logger.info(f"Subscribed to {topic} (QoS={qos})")

    def publish(
        self,
        topic: str,
        payload: dict | str,
        qos: int = 0,
        retain: bool = False,
    ) -> None:
        """Опубликовать сообщение.

        Args:
            topic: MQTT топик.
            payload: Сообщение (dict будет сериализован в JSON).
            qos: Уровень QoS.
            retain: Флаг retained сообщения.
        """
        if isinstance(payload, dict):
            payload = json.dumps(payload)

        self._client.publish(topic, payload, qos=qos, retain=retain)
        logger.debug(f"Published to {topic} (QoS={qos}, retain={retain})")

    @property
    def is_connected(self) -> bool:
        """True если клиент подключен к брокеру."""
        return self._connected
