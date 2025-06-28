import json
import re
import logging
from .entities import OpenWBBatSensor
from .entity_config import UNIT_MAP, ICON_MAP

_LOGGER = logging.getLogger(__name__)

def create_bat_entity(dev_id: str, topic: str, subkey: str, payload: str) -> list[OpenWBBatSensor] | OpenWBBatSensor | None:
    key = subkey.replace("/", "_").lower()

    pretty_key = key.replace("config_", "").replace("get_", "")
    pretty_key = pretty_key.replace("_", " ").title()

    unit = None
    icon = ICON_MAP.get("default")

    for pattern, u in UNIT_MAP.items():
        if pattern in key:
            unit = u
            break

    for pattern, i in ICON_MAP.items():
        if pattern in key:
            icon = i
            break

    try:
        parsed = json.loads(payload)
        if isinstance(parsed, list) and len(parsed) == 3 and all(isinstance(v, (int, float)) for v in parsed):
            return [
                OpenWBBatSensor(dev_id, f"{topic}/l1", f"{key}_l1", f"{pretty_key} L1", parsed[0], unit=unit, icon=icon, devtype="bat"),
                OpenWBBatSensor(dev_id, f"{topic}/l2", f"{key}_l2", f"{pretty_key} L2", parsed[1], unit=unit, icon=icon, devtype="bat"),
                OpenWBBatSensor(dev_id, f"{topic}/l3", f"{key}_l3", f"{pretty_key} L3", parsed[2], unit=unit, icon=icon, devtype="bat"),
            ]
    except Exception:
        pass

    try:
        value = float(payload)
    except Exception:
        value = payload.strip()
        if value.lower() in ("null", "none", ""):
            value = None

    return OpenWBBatSensor(
        dev_id=dev_id,
        topic=topic,
        key=key,
        pretty_name=pretty_key,
        initial_value=value,
        unit=unit,
        icon=icon,
        devtype="bat",
    )
