import logging
from ..const import DOMAIN
from ..cache.cache_device import get_device_info
from homeassistant.components.sensor import SensorEntity

_LOGGER = logging.getLogger(__name__)

class OpenWBCounterSensor(SensorEntity):
    def __init__(self, dev_id, topic, key, pretty_name, initial_value, unit=None, icon=None, devtype="counter"):
        self._topic = topic
        self._key = key
        self._dev_id = str(dev_id).lower()
        self._state = initial_value

        display_name = f"{devtype.upper()} {self._dev_id}"
        manufacturer = "openWB"
        model = f"openWB {devtype.title()}"

        if self._dev_id.isdigit():
            info = get_device_info(devtype, int(self._dev_id))
            if info:
                display_name = info.get("name", display_name)
                manufacturer = info.get("manufacturer", manufacturer)
                model = info.get("model", model)

        self._attr_name = f"openWB – {display_name} – {pretty_name}"
        self._attr_unique_id = f"openwb_{devtype}_{self._dev_id}_{key}"
        self._attr_suggested_object_id = self._attr_unique_id
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"openwb_{devtype}_{self._dev_id}")},
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
