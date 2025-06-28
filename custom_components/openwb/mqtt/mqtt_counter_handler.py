import re
import logging
from custom_components.openwb.counter.entity_factory import create_counter_entity

_LOGGER = logging.getLogger(__name__)

_sensors = {}
_async_add_entities = None

def init_counter_mqtt_handler(async_add_entities):
    global _async_add_entities
    _async_add_entities = async_add_entities

def is_counter_topic(topic: str) -> bool:
    return topic.startswith("openWB/counter/get/") or re.match(r"^openWB/counter/\d+/", topic)

async def handle_counter_topic(topic: str, payload: str):
    _LOGGER.debug(f"Handling counter topic: {topic} = {payload}")
    if _async_add_entities is None:
        _LOGGER.warning("Counter-MQTT-Handler nicht initialisiert.")
        return

    dev_id = "total"
    subkey = None

    if topic.startswith("openWB/counter/get/"):
        subkey = topic.split("openWB/counter/get/")[1]
    else:
        match = re.match(r"^openWB/counter/(\d+)/(.*)", topic)
        if match:
            dev_id, subkey = match.groups()

    if not subkey:
        _LOGGER.debug(f"Ignoriere Counter-Topic ohne subkey: {topic}")
        return

    try:
        entities = create_counter_entity(dev_id, topic, subkey, payload)
        if not entities:
            return
        if not isinstance(entities, list):
            entities = [entities]

        for entity in entities:
            uid = entity.unique_id
            if uid not in _sensors:
                _sensors[uid] = entity
                _async_add_entities([entity])
                _LOGGER.debug(f"Counter-Sensor angelegt: {uid}")
            else:
                _sensors[uid].update_state(entity.state)

    except Exception as e:
        _LOGGER.warning(f"Fehler beim Verarbeiten von Counter-Topic {topic}: {e}")
