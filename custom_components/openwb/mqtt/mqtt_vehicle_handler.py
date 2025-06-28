import re
import logging
import json
from custom_components.openwb.vehicle.entity_factory import create_vehicle_entity
from ..cache.cache_vehicle import update_vehicle_info
from homeassistant.components import mqtt

_LOGGER = logging.getLogger(__name__)

_sensors = {}
_async_add_entities = None

def init_vehicle_mqtt_handler(async_add_entities):
    global _async_add_entities
    _async_add_entities = async_add_entities

def is_vehicle_topic(topic: str) -> bool:
    return topic.startswith("openWB/vehicle/get/") or re.match(r"^openWB/vehicle/\d+/", topic)

def _parse_value(subkey: str, value: str):
    """Optional: Typisierung anhand des Keys."""
    try:
        if subkey.startswith("get/") or subkey in ("ev_template", "charge_template"):
            return int(value)
        if value.strip().lower() in ("true", "false"):
            return value.strip().lower() == "true"
        return float(value)
    except:
        return value.strip()

async def handle_vehicle_topic(topic: str, payload: str):
    _LOGGER.debug(f"Handling vehicle topic: {topic} = {payload}")
    if _async_add_entities is None:
        _LOGGER.warning("VEHICLE-MQTT-Handler nicht initialisiert.")
        return

    dev_id = "total"
    subkey = None

    if topic.startswith("openWB/vehicle/get/"):
        subkey = topic.split("openWB/vehicle/get/")[1]
    else:
        match = re.match(r"^openWB/vehicle/(\d+)/(.*)", topic)
        if match:
            dev_id, subkey = match.groups()

    if not subkey:
        _LOGGER.debug(f"Ignoriere Vehicle-Topic ohne subkey: {topic}")
        return

    # ✅ Fahrzeugdaten zwischenspeichern
    try:
        value = _parse_value(subkey, payload)
        update_vehicle_info(dev_id, **{subkey: value})
    except Exception as e:
        _LOGGER.warning(f"Fehler beim Update des Vehicle-Caches für {topic}: {e}")

    # ✅ Entität anlegen / aktualisieren
    try:
        entity = create_vehicle_entity(dev_id, topic, subkey, payload)
    
        # ➕ HIER: Select-Entitäten aus der Queue holen und registrieren
        from ..vehicle.entity_factory import drain_vehicle_entity_queue_by_type
        selects = drain_vehicle_entity_queue_by_type("select")
        if selects:
            _async_add_entities(selects)
    
        # Sensor-Entität ggf. registrieren
        if entity:
            uid = entity.unique_id
            if uid not in _sensors:
                _sensors[uid] = entity
                _async_add_entities([entity])
            else:
                _sensors[uid].update_state(entity.state)


    except Exception as e:
        _LOGGER.warning(f"Fehler beim Verarbeiten von VEHICLE-Topic {topic}: {e}")

async def subscribe_to_vehicle_info(hass):
    def handle_info(msg):
        topic = msg.topic
        payload = msg.payload
        match = re.match(r"^openWB/vehicle/(\d+)/info$", topic)
        if not match:
            return
        vehicle_id = match.group(1)
        try:
            data = json.loads(payload)
            update_vehicle_info(vehicle_id, **data)
            _LOGGER.debug(f"Vehicle info geladen für ID {vehicle_id}: {data}")
        except Exception as e:
            _LOGGER.warning(f"Fehler beim Verarbeiten von vehicle/info: {e}")

    await mqtt.async_subscribe(hass, "openWB/vehicle/+/info", handle_info)