import logging
import re
import json
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.mqtt import async_subscribe
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, MQTT_PREFIX
from .cache.cache_template import (
    update_charge_template_name,
    update_ev_template_name,
    get_charge_template_name,
    get_ev_template_name,
)
from .cache.cache_device import get_device_info
from .cache.cache_vehicle import get_vehicle_info
from .cache.cache_chargepoint import get_chargepoint_info

from .mqtt.mqtt_pv_handler import is_pv_topic, handle_pv_topic, init_pv_mqtt_handler
from .mqtt.mqtt_bat_handler import is_bat_topic, handle_bat_topic, init_bat_mqtt_handler
from .mqtt.mqtt_counter_handler import is_counter_topic, handle_counter_topic, init_counter_mqtt_handler
from .mqtt.mqtt_vehicle_handler import is_vehicle_topic, handle_vehicle_topic, init_vehicle_mqtt_handler
from .mqtt.mqtt_chargepoint_handler import is_chargepoint_topic, handle_chargepoint_topic, init_chargepoint_mqtt_handler

_LOGGER = logging.getLogger(__name__)
COUNTER_BASE = f"{MQTT_PREFIX}/counter/"
PV_BASE = f"{MQTT_PREFIX}/pv/"
BAT_BASE = f"{MQTT_PREFIX}/bat/"
CHARGEPOINT_BASE = f"{MQTT_PREFIX}/chargepoint/"
VEHICLE_BASE = f"{MQTT_PREFIX}/vehicle/"

def parse_float(value):
    try:
        if value is None or value.strip().lower() in ("null", "none", ""):
            return None
        return float(value)
    except (ValueError, TypeError):
        return None

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    sensors = {}

    init_pv_mqtt_handler(async_add_entities)
    init_bat_mqtt_handler(async_add_entities)
    init_counter_mqtt_handler(async_add_entities)
    init_vehicle_mqtt_handler(async_add_entities)
    init_chargepoint_mqtt_handler(async_add_entities)

    async def mqtt_message_received(msg):
        topic = msg.topic
        payload = msg.payload
        _LOGGER.debug(f"MQTT received: {topic} = {payload}")

        if "/set" in topic:
            _LOGGER.debug(f"Ignore set-topic: {topic}")
            return

        if is_pv_topic(topic):
            await handle_pv_topic(topic, payload)
            return

        if is_bat_topic(topic):
            await handle_bat_topic(topic, payload)
            return
        
        if is_counter_topic(topic):
            await handle_counter_topic(topic, payload)
            return
        
        if is_vehicle_topic(topic):
            await handle_vehicle_topic(topic, payload)
            return

        if is_chargepoint_topic(topic):
            await handle_chargepoint_topic(topic, payload)
            return

    await async_subscribe(hass, f"{MQTT_PREFIX}/#", mqtt_message_received)


from .cache.cache_device import get_device_info

class OpenWBBaseSensor(SensorEntity):
    def __init__(self, dev_id, topic, key, initial_value, unit: str = None, icon: str = None, devtype: str = "device"):
        self._topic = topic
        self._key = key
        self._dev_id = str(dev_id).lower()
        self._state = initial_value

        # Defaultwerte
        display_name = f"{devtype.upper()} {self._dev_id}"
        manufacturer = "openWB"
        model = "openWB Device"

        if self._dev_id.isdigit():
            dev_id_int = int(self._dev_id)
            MQTT_TO_CONFIG_TYPE = {
                "counter": "counter",
                "pv": "inverter",
                "bat": "bat",
                "vehicle": "vehicle",
                "chargepoint": "chargepoint",
            }
            config_type = MQTT_TO_CONFIG_TYPE.get(devtype, devtype)

            if devtype == "vehicle":
                info = get_vehicle_info(dev_id_int)
            elif devtype == "chargepoint":
                info = get_chargepoint_info(dev_id_int)
            else:
                info = get_device_info(config_type, dev_id_int)

            if info:
                if info.get("name"):
                    display_name = info["name"]
                if info.get("manufacturer"):
                    manufacturer = info["manufacturer"]
                if info.get("model"):
                    model = info["model"]

        self._attr_name = f"openWB - {display_name} - {key.replace('_', ' ').title()}"
        self._attr_unique_id = f"openwb_{devtype.lower()}_{self._dev_id}_{key}"
        self._attr_suggested_object_id = self._attr_unique_id
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"openwb_{devtype.lower()}_{self._dev_id}")},
            "name": f"openWB – {devtype.upper()} - {display_name} (ID: {self._dev_id})",
            "manufacturer": manufacturer,
            "model": model,
        }

    @property
    def state(self):
        return self._state

    def update_state(self, value):
        self._state = value
        self.async_write_ha_state()

