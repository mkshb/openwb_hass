import re
import json
import logging
from ..chargepoint.entity_factory import create_chargepoint_entity
from ..cache.cache_chargepoint import update_chargepoint_info

_LOGGER = logging.getLogger(__name__)

_sensors = {}
_async_add_entities = None


CHARGEPOINT_INFO_TOPIC = "openWB/chargepoint/+/config"

def subscribe_to_chargepoint_info(mqtt_client):
    mqtt_client.async_subscribe(CHARGEPOINT_INFO_TOPIC, _handle_chargepoint_config_message, 0)

def _handle_chargepoint_config_message(msg):
    topic = msg.topic
    payload = msg.payload

    match = re.match(r"openWB/chargepoint/(\d+)/config", topic)
    if not match:
        _LOGGER.debug(f"Ignoring non-matching config topic: {topic}")
        return

    chargepoint_id = int(match.group(1))

    try:
        config = json.loads(payload.decode("utf-8"))
        name = config.get("name")
        info = config.get("info", {}) or {}
        model = info.get("model")
        manufacturer = "openWB"

        update_chargepoint_info(chargepoint_id, {
            "name": name,
            "manufacturer": manufacturer,
            "model": model
        })
        _LOGGER.debug(f"Chargepoint {chargepoint_id} config updated: {name}, {manufacturer}, {model}")
    except Exception as e:
        _LOGGER.warning(f"Error processing chargepoint config {topic}: {e}")

def init_chargepoint_mqtt_handler(async_add_entities):
    global _async_add_entities
    _async_add_entities = async_add_entities


def is_chargepoint_topic(topic: str) -> bool:
    return topic.startswith("openWB/chargepoint/get/") or re.match(r"^openWB/chargepoint/\d+/", topic)


async def handle_chargepoint_topic(topic: str, payload: str):
    _LOGGER.debug(f"Handling chargepoint topic: {topic} = {payload}")
    if _async_add_entities is None:
        _LOGGER.warning("CHARGEPOINT-MQTT-Handler nicht initialisiert.")
        return

    dev_id = "total"
    subkey = None

    if topic.startswith("openWB/chargepoint/get/"):
        subkey = topic.split("openWB/chargepoint/get/")[1]
    else:
        match = re.match(r"^openWB/chargepoint/(\d+)/(.*)", topic)
        if match:
            dev_id, subkey = match.groups()

    if not subkey:
        _LOGGER.debug(f"Ignoriere Chargepoint-Topic ohne subkey: {topic}")
        return

    if topic.endswith("/config"):
        match = re.match(r"^openWB/chargepoint/(\d+)/config", topic)
        if not match:
            return
        dev_id = match.group(1)
    
        try:
            import json
            from ..chargepoint.entities import OpenWBChargepointSensor
            from ..cache.cache_chargepoint import update_chargepoint_info  # << Stelle sicher, dass das korrekt ist
    
            data = json.loads(payload)

            # Cache nur mit flacher Struktur befüllen
            name = data.get("name", f"Chargepoint {dev_id}")
            manufacturer = "openWB"
            model = data.get("type", "openWB Chargepoint")
            
            from ..cache.cache_chargepoint import update_chargepoint_info
            update_chargepoint_info(int(dev_id), {
                "name": name,
                "manufacturer": manufacturer,
                "model": model
            })
    
            # 🔁 Danach wie gehabt flatten:
            def flatten(d: dict, parent: str = "") -> dict:
                result = {}
                for k, v in d.items():
                    key = f"{parent}_{k}" if parent else k
                    if isinstance(v, dict):
                        result.update(flatten(v, key))
                    else:
                        result[key.lower()] = v
                return result
    
            flat = flatten(data)
    
            for key, value in flat.items():
                uid = f"openwb_chargepoint_{dev_id}_{key}"
                if uid not in _sensors:
                    pretty_name = key.replace("_", " ").title()
                    sensor = OpenWBChargepointSensor(dev_id, topic, key, pretty_name, initial_value=value)
                    _sensors[uid] = sensor
                    _async_add_entities([sensor])
                else:
                    _sensors[uid].update_state(value)
    
        except Exception as e:
            _LOGGER.warning(f"Fehler beim Verarbeiten von chargepoint/config ({payload}) für {topic}: {e}")
        return

    try:
        entity = create_chargepoint_entity(dev_id, topic, subkey, payload)
        if entity:
            if isinstance(entity, list):
                for e in entity:
                    uid = e.unique_id
                    if uid not in _sensors:
                        _sensors[uid] = e
                        _async_add_entities([e])
                    else:
                        _sensors[uid].update_state(e.state)
            else:
                uid = entity.unique_id
                if uid not in _sensors:
                    _sensors[uid] = entity
                    _async_add_entities([entity])
                else:
                    _sensors[uid].update_state(entity.state)
    except Exception as e:
        _LOGGER.warning(f"Fehler beim Verarbeiten von CHARGEPOINT-Topic {topic}: {e}")
