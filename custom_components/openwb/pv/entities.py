import logging
from homeassistant.components.sensor import SensorEntity
from ..const import DOMAIN
from ..cache.cache_device import get_device_info

_LOGGER = logging.getLogger(__name__)


class OpenWBPVSensor(SensorEntity):
    def __init__(self, dev_id, topic, key, pretty_name, initial_value, unit=None, icon=None, devtype="pv"):
        self._topic = topic
        self._key = key
        self._dev_id = str(dev_id).lower()
        self._state = initial_value

        # Standardwerte
        display_name = f"PV {self._dev_id}"
        manufacturer = "openWB"
        model = "openWB PV"

        if self._dev_id.isdigit():
            dev_id_int = int(self._dev_id)
            info = get_device_info("inverter", dev_id_int)
            if info:
                display_name = info.get("name", display_name)
                manufacturer = info.get("manufacturer", manufacturer)
                model = info.get("model", model)

        self._attr_name = f"openWB – {display_name} – {pretty_name}"
        self._attr_unique_id = f"openwb_pv_{self._dev_id}_{key}"
        self._attr_suggested_object_id = self._attr_unique_id
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"openwb_pv_{self._dev_id}")},
            "name": f"openWB – PV - {display_name} (ID: {self._dev_id})",
            "manufacturer": manufacturer,
            "model": model,
        }

    @property
    def state(self):
        return self._state

    def update_state(self, value):
        self._state = value
        self.async_write_ha_state()
