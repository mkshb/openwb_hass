import logging
import re
from ..const import DOMAIN
from ..cache.cache_chargepoint import get_chargepoint_info
from homeassistant.util import slugify
from homeassistant.components.sensor import SensorEntity
from .entity_config import SENSOR_DEFINITION_MAP

_LOGGER = logging.getLogger(__name__)

def clean_label(value: str) -> str:
    """Bereinigt sichtbare Namen (UI), z. B. entfernt + und Sonderzeichen"""
    return re.sub(r"[^\w\s\-\(\)]", "", value).strip()

def clean_id(value: str) -> str:
    """Erzeugt maschinenlesbare ID (z. B. für unique_id, identifiers)"""
    return slugify(value)

class OpenWBChargepointSensor(SensorEntity):
    def __init__(self, dev_id, topic, key, pretty_name, initial_value=None, unit=None, icon=None, devtype="chargepoint"):
        self._topic = topic
        self._key = key
        self._dev_id = str(dev_id).lower()
        self._state = initial_value

        # Defaultwerte
        display_name = f"{devtype.upper()} {self._dev_id}"
        manufacturer = "openWB"
        model = f"openWB {devtype.title()}"

        # Zusätzliche Infos aus dem Cache holen
        if self._dev_id.isdigit():
            info = get_chargepoint_info(int(self._dev_id)) or {}

            raw_name = info.get("name")
            if isinstance(raw_name, str) and raw_name.strip():
                display_name = clean_label(raw_name)

            raw_manufacturer = info.get("manufacturer")
            if isinstance(raw_manufacturer, str):
                manufacturer = clean_label(raw_manufacturer)

            raw_model = info.get("model")
            if isinstance(raw_model, str):
                model = clean_label(raw_model)

        # Geräte-ID absichern (z. B. falls Sonderzeichen enthalten sind)
        safe_dev_id = clean_id(f"{devtype}_{self._dev_id}")

        # Sensor-Metadaten aus zentraler Map laden
        definition = SENSOR_DEFINITION_MAP.get(key, SENSOR_DEFINITION_MAP["default"])
        resolved_unit = definition.get("unit")
        resolved_icon = definition.get("icon", SENSOR_DEFINITION_MAP["default"]["icon"])

        # Sensor-Attribute setzen
        self._attr_name = f"openWB – {display_name} – {pretty_name}"
        self._attr_unique_id = f"openwb_{safe_dev_id}_{key}"
        self._attr_suggested_object_id = self._attr_unique_id
        self._attr_native_unit_of_measurement = resolved_unit
        self._attr_device_class = definition.get("device_class")
        self._attr_state_class = definition.get("state_class")
        self._attr_icon = icon or resolved_icon

        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"openwb_{safe_dev_id}")},
            "name": f"openWB – {devtype.upper()} – {display_name} (ID: {self._dev_id})",
            "manufacturer": manufacturer,
            "model": model,
        }

    @property
    def state(self):
        return self._state

    def update_state(self, value):
        self._state = value
        self.async_write_ha_state()
