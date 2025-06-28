import re
import logging
from custom_components.openwb.bat.entity_factory import create_bat_entity

_LOGGER = logging.getLogger(__name__)

_sensors = {}
_async_add_entities = None


def init_bat_mqtt_handler(async_add_entities):
    global _async_add_entities
    _async_add_entities = async_add_entities


def is_bat_topic(topic: str) -> bool:
    return topic.startswith("openWB/bat/get/") or re.match(r"^openWB/bat/\d+/", topic)


async def handle_bat_topic(topic: str, payload: str):
    _LOGGER.debug(f"Handling battery topic: {topic} = {payload}")
    if _async_add_entities is None:
        _LOGGER.warning("BAT-MQTT-Handler nicht initialisiert.")
        return

    dev_id = "total"
    subkey = None

    if topic.startswith("openWB/bat/get/"):
        subkey = topic.split("openWB/bat/get/")[1]
    else:
        match = re.match(r"^openWB/bat/(\d+)/(.*)", topic)
        if match:
            dev_id, subkey = match.groups()

    if not subkey:
        _LOGGER.debug(f"Ignoriere Batterie-Topic ohne subkey: {topic}")
        return

    try:
        entities = create_bat_entity(dev_id, topic, subkey, payload)

        if not entities:
            return
        
        if not isinstance(entities, list):
            entities = [entities]
        
        for entity in entities:
            uid = entity.unique_id
            if uid not in _sensors:
                _sensors[uid] = entity
                _async_add_entities([entity])
                _LOGGER.debug(f"BAT-Sensor angelegt: {uid}")
            else:
                _sensors[uid].update_state(entity.state)
    except Exception as e:
        _LOGGER.warning(f"Fehler beim Verarbeiten von BAT-Topic {topic}: {e}")
