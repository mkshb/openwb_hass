import logging

_LOGGER = logging.getLogger(__name__)

def send_mqtt_message(hass, topic: str, payload: str):
    _LOGGER.info(f"Sende MQTT: {topic} = {payload}")
    mqtt = hass.data["mqtt"]
    mqtt.async_publish(topic, payload, qos=0, retain=False)