import logging
from homeassistant.components.sensor import SensorEntity
from ..const import DOMAIN
from ..cache.cache_vehicle import get_vehicle_info

_LOGGER = logging.getLogger(__name__)


class OpenWBVehicleSensor(SensorEntity):
    def __init__(self, dev_id, topic, key, initial_value, unit=None, icon=None):
        self._topic = topic
        self._key = key
        self._dev_id = str(dev_id).lower()
        self._state = initial_value

        display_name = f"Vehicle {self._dev_id}"
        manufacturer = "openWB"
        model = "EV"

        if self._dev_id.isdigit():
            info = get_vehicle_info(int(self._dev_id))
            if info:
                display_name = info.get("name", display_name)
                manufacturer = info.get("manufacturer", manufacturer)
                model = info.get("model", model)

        #self._attr_name = f"openWB – {display_name} – {key.replace('_', ' ').title()}"
        self._attr_unique_id = f"openwb_vehicle_{self._dev_id}_{key}"
        self._attr_suggested_object_id = self._attr_unique_id
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"openwb_vehicle_{self._dev_id}")},
            "name": f"openWB – Vehicle – {display_name} (ID: {self._dev_id})",
            "manufacturer": manufacturer,
            "model": model,
        }


    @property
    def state(self):
        return self._state
    
    @property
    def name(self):
        info = get_vehicle_info(int(self._dev_id)) if self._dev_id.isdigit() else None
        display_name = info.get("name") if info and "name" in info else f"Vehicle {self._dev_id}"
        full_name = f"openWB – {display_name} – {self._key.replace('_', ' ').title()}"
        return full_name

    def update_state(self, value):
        self._state = value
        info = get_vehicle_info(self._dev_id)
        if info:
            new_display_name = info.get("name")
            if new_display_name:
                self._attr_name = f"openWB – {new_display_name} – {self._key.replace('_', ' ').title()}"
    
        self.async_write_ha_state()

