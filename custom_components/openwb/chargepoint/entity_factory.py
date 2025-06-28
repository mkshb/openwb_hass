import json
import logging
from .entities import OpenWBChargepointSensor
from .entity_config import UNIT_MAP, ICON_MAP

_LOGGER = logging.getLogger(__name__)

def create_chargepoint_entity(dev_id: str, topic: str, subkey: str, payload: str) -> list[OpenWBChargepointSensor] | OpenWBChargepointSensor | None:
    key = subkey.replace("/", "_").lower()
    pretty_key = key.replace("config_", "").replace("get_", "").replace("_", " ").title()

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

    # Phasenwerte (z. B. [1.2, 1.3, 1.4])
    try:
        parsed = json.loads(payload)
        if isinstance(parsed, list) and len(parsed) == 3 and all(isinstance(v, (int, float)) for v in parsed):
            return [
                OpenWBChargepointSensor(dev_id, f"{topic}/l1", f"{key}_l1", f"{pretty_key} L1", parsed[0], unit=unit, icon=icon, devtype="chargepoint"),
                OpenWBChargepointSensor(dev_id, f"{topic}/l2", f"{key}_l2", f"{pretty_key} L2", parsed[1], unit=unit, icon=icon, devtype="chargepoint"),
                OpenWBChargepointSensor(dev_id, f"{topic}/l3", f"{key}_l3", f"{pretty_key} L3", parsed[2], unit=unit, icon=icon, devtype="chargepoint"),
            ]
        elif isinstance(parsed, dict):
            entities = []
            for k, v in parsed.items():
                full_key = f"{key}_{k}".lower()
                pretty = f"{pretty_key} {k.replace('_', ' ').title()}"
                if isinstance(v, bool):
                    pretty += f" – {str(v).title()}"

                if isinstance(v, (int, float, str, bool)) or v is None:
                    entities.append(OpenWBChargepointSensor(
                        dev_id,
                        f"{topic}/{k}",
                        full_key,
                        pretty,
                        initial_value=v,
                        unit=UNIT_MAP.get(k),
                        icon=ICON_MAP.get(k),
                        devtype="chargepoint"
                    ))
                elif isinstance(v, dict):
                    for sub_k, sub_v in v.items():
                        sub_key = f"{full_key}_{sub_k}".lower()
                        sub_pretty = f"{pretty} {sub_k.replace('_', ' ').title()}"
                        if isinstance(sub_v, bool):
                            sub_pretty += f" – {str(sub_v).title()}"

                        if isinstance(sub_v, (int, float, str, bool)) or sub_v is None:
                            entities.append(OpenWBChargepointSensor(
                                dev_id,
                                f"{topic}/{k}/{sub_k}",
                                sub_key,
                                sub_pretty,
                                initial_value=sub_v,
                                unit=UNIT_MAP.get(sub_k),
                                icon=ICON_MAP.get(sub_k),
                                devtype="chargepoint"
                            ))
                        else:
                            _LOGGER.debug("Überspringe nicht unterstützten Sub-Wert (%s): %s", sub_k, sub_v)
            return entities
    except Exception as e:
        _LOGGER.debug(f"Kein JSON oder Fehler beim Parsen von {topic}: {e}")

    # Fallback für einfache Einzelwerte
    try:
        value = float(payload)
    except Exception:
        value = payload.strip()
        if value.lower() in ("null", "none", ""):
            value = None

    return OpenWBChargepointSensor(
        dev_id=dev_id,
        topic=topic,
        key=key,
        pretty_name=pretty_key,
        initial_value=value,
        unit=unit,
        icon=icon,
        devtype="chargepoint",
    )
