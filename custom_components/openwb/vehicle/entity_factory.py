import logging
from .entities import OpenWBVehicleSensor
from .entity_config import UNIT_MAP, ICON_MAP

_LOGGER = logging.getLogger(__name__)

_entity_queue = {
    "sensor": [],
    "select": [],
}

def create_vehicle_entity(dev_id: str, topic: str, subkey: str, payload: str):
    key = subkey.replace("/", "_").lower()

    try:
        value = float(payload)
    except Exception:
        value = payload.strip()
        if value.lower() in ("null", "none", ""):
            value = None

    unit = next((u for k, u in UNIT_MAP.items() if k in key), None)
    icon = next((i for k, i in ICON_MAP.items() if k in key), ICON_MAP.get("default"))

    return OpenWBVehicleSensor(dev_id, topic, key, value, unit=unit, icon=icon)
    
def drain_vehicle_entity_queue_by_type(entity_type: str):
    if entity_type not in _entity_queue:
        return []
    ents = _entity_queue[entity_type]
    _entity_queue[entity_type] = []
    return ents