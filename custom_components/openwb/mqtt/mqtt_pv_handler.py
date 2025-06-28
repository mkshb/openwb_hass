import re
import logging
from custom_components.openwb.pv.entity_factory import create_pv_entity

_LOGGER = logging.getLogger(__name__)

_sensors = {}
_async_add_entities = None


def init_pv_mqtt_handler(async_add_entities):
    global _async_add_entities
    _async_add_entities = async_add_entities


def is_pv_topic(topic: str) -> bool:
    return topic.startswith("openWB/pv/get/") or re.match(r"^openWB/pv/\d+/", topic)


async def handle_pv_topic(topic: str, payload: str):
    _LOGGER.debug(f"Handling PV topic: {topic} = {payload}")
    if _async_add_entities is None:
        _LOGGER.warning("PV-MQTT-Handler nicht initialisiert.")
        return

    dev_id = "total"
    subkey = None

    if topic.startswith("openWB/pv/get/"):
        subkey = topic.split("openWB/pv/get/")[1]
    else:
        match = re.match(r"^openWB/pv/(\d+)/(.*)", topic)
        if match:
            dev_id, subkey = match.groups()

    if not subkey:
        _LOGGER.debug(f"Ignoriere PV-Topic ohne subkey: {topic}")
        return

    try:
        entities = create_pv_entity(dev_id, topic, subkey, payload)

        if not entities:
            return
        
        # Falls einzelne Entität → mache zur Liste
        if not isinstance(entities, list):
            entities = [entities]
        
        for entity in entities:
            uid = entity.unique_id
            if uid not in _sensors:
                _sensors[uid] = entity
                _async_add_entities([entity])
                _LOGGER.debug(f"PV-Sensor angelegt: {uid}")
            else:
                _sensors[uid].update_state(entity.state)

    except Exception as e:
        _LOGGER.warning(f"Fehler beim Verarbeiten von PV-Topic {topic}: {e}")
