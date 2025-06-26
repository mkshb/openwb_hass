import logging
import re
import json
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.mqtt import async_subscribe
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, MQTT_PREFIX
from .template_cache import (
    update_charge_template_name,
    update_ev_template_name,
    get_charge_template_name,
    get_ev_template_name,
)
from .select import SELECT_ENTITIES
from .device_cache import get_device_info
from .vehicle_cache import get_vehicle_info
from .chargepoint_cache import get_chargepoint_info

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

    async def mqtt_message_received(msg):
        topic = msg.topic
        payload = msg.payload
        _LOGGER.debug(f"MQTT received: {topic} = {payload}")

        if "/set" in topic:
            _LOGGER.debug(f"Ignore set-topic: {topic}")
            return

        # --- Chargepoint Config openWB/chargepoint/<id>/config ---
        if topic.startswith(f"{MQTT_PREFIX}/chargepoint/") and topic.endswith("/config"):
            match = re.match(rf"{MQTT_PREFIX}/chargepoint/(\d+)/config", topic)
            if not match:
                return
            dev_id = match.group(1)
            try:
                data = json.loads(payload)
                for key, value in data.items():
                    if isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            sensor_key = f"{key}_{subkey}".lower()
                            sensor_id = f"openwb_chargepoint_{dev_id}_{sensor_key}"
                            if sensor_id not in sensors:
                                sensor = OpenWBChargepointSensor(dev_id, topic, sensor_key, subvalue)
                                sensors[sensor_id] = sensor
                                async_add_entities([sensor])
                            else:
                                sensors[sensor_id].update_state(subvalue)
                    else:
                        sensor_key = key.lower()
                        sensor_id = f"openwb_chargepoint_{dev_id}_{sensor_key}"
                        if sensor_id not in sensors:
                            sensor = OpenWBChargepointSensor(dev_id, topic, sensor_key, value)
                            sensors[sensor_id] = sensor
                            async_add_entities([sensor])
                        else:
                            sensors[sensor_id].update_state(value)
            except Exception as e:
                _LOGGER.warning(f"Fehler beim Parsen von chargepoint config ({payload}) für {topic}: {e}")
            return

        # --- Save template definitions ---
        if topic.startswith(f"{MQTT_PREFIX}/vehicle/template/charge_template/"):
            try:
                if payload.strip().startswith("{"):
                    data = json.loads(payload)
                    template_id = str(data["id"])
                    template_name = data.get("name", f"Template {template_id}")
                else:
                    template_id = str(payload).strip()
                    template_name = f"Template {template_id}"
                update_charge_template_name(template_id, template_name)
                _LOGGER.debug(f"Charge-Template gespeichert: {template_id} = {template_name}")
            except Exception as e:
                _LOGGER.warning(f"Fehler beim Parsen von charge_template Definition ({payload}): {e}")
            return

        elif topic.startswith(f"{MQTT_PREFIX}/vehicle/template/ev_template/"):
            try:
                match = re.match(rf"{MQTT_PREFIX}/vehicle/template/ev_template/(\d+)", topic)
                if match:
                    template_id = match.group(1)
                    payload_dict = json.loads(payload)
                    name = payload_dict.get("name", f"EV Template {template_id}")
                    update_ev_template_name(template_id, name)
                    _LOGGER.debug(f"EV-Template gespeichert: {template_id} = {name}")
            except Exception as e:
                _LOGGER.warning(f"Fehler beim Parsen von ev_template Definition ({payload}): {e}")
            return

        # --- Summeries openWB/bat/get ---
        if topic.startswith(f"{MQTT_PREFIX}/bat/get/"):
            subkey = topic.split("/bat/get/")[1]
            key = subkey.replace("/", "_").lower()
            unique_id = f"openwb_bat_total_{key}"

            unit = None
            icon = "mdi:battery"
            try:
                if re.match(r"^-?\d+(\.\d+)?$", payload.strip()):
                    value = float(payload)
                else:
                    value = payload.strip() 
                    unit = None
                    icon = "mdi:alert-circle-outline"
                if "soc" in key:
                    unit = "%"
                elif "imported" in key or "exported" in key:
                    value = value / 1000.0
                    unit = "kWh"
                    icon = "mdi:transmission-tower"
                elif "power" in key or "current" in key:
                    unit = "W"
                    icon = "mdi:lightning-bolt"

                if unique_id not in sensors:
                    sensor = OpenWBBatSensor("total", topic, key, value, unit=unit, icon=icon)
                    sensors[unique_id] = sensor
                    async_add_entities([sensor])
                else:
                    sensors[unique_id].update_state(value)
            except Exception as e:
                _LOGGER.warning(f"Error parsing totals ({payload}) for {topic}: {e}")
            return

        # --- Summeries openWB/pv/get ---
        if topic.startswith(f"{MQTT_PREFIX}/pv/get/"):
            subkey = topic.split("/pv/get/")[1]
            key = subkey.replace("/", "_").lower()
            unique_id = f"openwb_pv_total_{key}"
        
            unit = None
            icon = "mdi:solar-power"
            try:
                if re.match(r"^-?\d+(\.\d+)?$", payload.strip()):
                    value = float(payload)
                else:
                    value = payload.strip()
                    unit = None
                    icon = "mdi:alert-circle-outline"
        
                if isinstance(value, float):
                    if "imported" in key or "exported" in key:
                        value = value / 1000.0
                        unit = "kWh"
                        icon = "mdi:transmission-tower"
                    elif "power" in key or "current" in key:
                        unit = "W"
                        icon = "mdi:lightning-bolt"
        
                if unique_id not in sensors:
                    sensor = OpenWBPVSensor("total", topic, key, value, unit=unit, icon=icon)
                    sensors[unique_id] = sensor
                    async_add_entities([sensor])
                else:
                    sensors[unique_id].update_state(value)
            except Exception as e:
                _LOGGER.warning(f"Error parsing totals ({payload}) for {topic}: {e}")
            return
        

        if topic.startswith(COUNTER_BASE):
            prefix = COUNTER_BASE
            entity_cls = OpenWBCounterSensor
            domain = "counter"
        elif topic.startswith(PV_BASE):
            prefix = PV_BASE
            entity_cls = OpenWBPVSensor
            domain = "pv"
        elif topic.startswith(BAT_BASE):
            prefix = BAT_BASE
            entity_cls = OpenWBBatSensor
            domain = "bat"
        elif topic.startswith(CHARGEPOINT_BASE):
            prefix = CHARGEPOINT_BASE
            entity_cls = OpenWBChargepointSensor
            domain = "chargepoint"
        elif topic.startswith(VEHICLE_BASE):
            prefix = VEHICLE_BASE
            entity_cls = OpenWBVehicleSensor
            domain = "vehicle"
        else:
            return

        match = re.match(rf"{re.escape(prefix)}(\d+)/(.*)", topic)
        if not match:
            return

        dev_id, subkey = match.groups()
        key = subkey.replace("/", "_").lower()
        unique_id = f"openwb_{domain}_{dev_id}_{key}"

        # --- Vehicle special cases---
        if domain == "vehicle":
            if subkey.startswith("soc_module"):
                _LOGGER.debug(f"Ignoriere soc_module-Wert für {topic}")
                return

            if subkey == "charge_template":
                template_id = payload.strip()
                template_name = get_charge_template_name(template_id) or f"Template {template_id}"

                # Create and update enities for charge templates
                if unique_id not in sensors:
                    sensor = entity_cls(dev_id, topic, key, template_name, icon="mdi:playlist-check")
                    sensors[unique_id] = sensor
                    async_add_entities([sensor])
                else:
                    sensors[unique_id].update_state(template_name)
            
                # Update selectors
                for selector in SELECT_ENTITIES:
                    if selector._vehicle_id == str(dev_id):
                        selector.update_current_option_by_id(template_id)
                return

            elif subkey == "ev_template":
                template_id = payload.strip()
                template_name = get_ev_template_name(template_id) or f"EV Template {template_id}"
                if unique_id not in sensors:
                    sensor = entity_cls(dev_id, topic, key, template_name, icon="mdi:car-electric")
                    sensors[unique_id] = sensor
                    async_add_entities([sensor])
                else:
                    sensors[unique_id].update_state(template_name)
                return

            elif subkey == "info":
                try:
                    info = json.loads(payload)
                    for info_key, info_value in info.items():
                        info_sensor_key = f"{key}_{info_key}".lower()
                        info_sensor_id = f"openwb_{domain}_{dev_id}_{info_sensor_key}"
                        if info_sensor_id not in sensors:
                            sensor = entity_cls(dev_id, topic, info_sensor_key, info_value, unit=None, icon="mdi:car-info")
                            sensors[info_sensor_id] = sensor
                            async_add_entities([sensor])
                        else:
                            sensors[info_sensor_id].update_state(info_value)
                except Exception as e:
                    _LOGGER.warning(f"Fehler beim Parsen von vehicle info JSON ({payload}) für {topic}: {e}")
                return

        # --- List values ---
        if subkey.endswith(("max_currents", "currents", "powers", "voltages", "power_factors")):
            try:
                values = json.loads(payload)
                phases = ["l1", "l2", "l3"]
                unit = {
                    "currents": "A", "max_currents": "A", "powers": "A", "voltages": "V"
                }.get(subkey.split("/")[-1], None)
                icon = {
                    "currents": "mdi:current-ac",
                    "max_currents": "mdi:current-ac",
                    "powers": "mdi:current-ac",
                    "voltages": "mdi:flash",
                    "power_factors": "mdi:sine-wave",
                }.get(subkey.split("/")[-1], None)
                for idx, phase in enumerate(phases):
                    phase_key = f"{key}_{phase}"
                    phase_id = f"openwb_{domain}_{dev_id}_{phase_key}"
                    if phase_id not in sensors:
                        sensor = entity_cls(dev_id, topic, phase_key, values[idx], unit=unit, icon=icon)
                        sensors[phase_id] = sensor
                        async_add_entities([sensor])
                    else:
                        sensors[phase_id].update_state(values[idx])
            except Exception as e:
                _LOGGER.warning(f"Error parsing list ({payload}) for {topic}: {e}")
            return

        # --- Single values ---
        icon = None
        unit = None
        try:
            if subkey.endswith(("power", "max_power_errorcase", "max_total_power", "config/max_ac_out")):
                value = parse_float(payload)
                unit = "W"
                icon = "mdi:lightning-bolt"
            elif subkey in ("get/imported", "get/exported", "get/daily_imported", "get/daily_exported", "get/monthly_exported", "get/yearly_exported"):
                value = float(payload) / 1000.0
                unit = "kWh"
                icon = "mdi:transmission-tower"
            elif subkey == "get/frequency":
                value = parse_float(payload)
                unit = "Hz"
                icon = "mdi:sine-wave"
            elif subkey == "get/soc":
                value = parse_float(payload)
                unit = "%"
                icon = "mdi:battery"
            else:
                value = payload
        except Exception as e:
            _LOGGER.warning(f"Error parsing value ({payload}) for {topic}: {e}")
            return

        if unique_id not in sensors:
            sensor = entity_cls(dev_id, topic, key, value, unit=unit, icon=icon)
            sensors[unique_id] = sensor
            async_add_entities([sensor])
        else:
            sensors[unique_id].update_state(value)

    await async_subscribe(hass, f"{MQTT_PREFIX}/#", mqtt_message_received)


from .device_cache import get_device_info

class OpenWBBaseSensor(SensorEntity):
    def __init__(self, dev_id, topic, key, initial_value, unit: str = None, icon: str = None, devtype: str = "device"):
        self._topic = topic
        self._key = key
        self._dev_id = dev_id
        self._state = initial_value

        # Gerätedaten abrufen (nur falls dev_id eine Zahl ist)
        device_name = f"{devtype.upper()} {dev_id}"
        manufacturer = "openWB"
        model = "openWB Device"

        if isinstance(dev_id, int) or (isinstance(dev_id, str) and dev_id.isdigit()):
            dev_id_int = int(dev_id)

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
                    device_name = info["name"]
                if info.get("manufacturer"):
                    manufacturer = info["manufacturer"]
                if info.get("model"):
                    model = info["model"]

        self._attr_name = f"openWB - {device_name} - {key.replace('_', ' ').title()}"
        self._attr_unique_id = f"openwb_{devtype.lower()}_{dev_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"openwb_{devtype.lower()}_{dev_id}")},
            "name": f"openWB – {devtype.upper()} - {device_name} (ID: {dev_id})",
            "manufacturer": manufacturer,
            "model": model,
        }

    @property
    def state(self):
        return self._state

    def update_state(self, value):
        self._state = value
        self.async_write_ha_state()


class OpenWBCounterSensor(OpenWBBaseSensor):
    def __init__(self, dev_id, topic, key, initial_value, unit=None, icon=None):
        super().__init__(dev_id, topic, key, initial_value, unit, icon, devtype="counter")


class OpenWBPVSensor(OpenWBBaseSensor):
    def __init__(self, dev_id, topic, key, initial_value, unit=None, icon=None):
        super().__init__(dev_id, topic, key, initial_value, unit, icon, devtype="pv")

class OpenWBBatSensor(OpenWBBaseSensor):
    def __init__(self, dev_id, topic, key, initial_value, unit=None, icon=None):
        super().__init__(dev_id, topic, key, initial_value, unit, icon, devtype="bat")

class OpenWBChargepointSensor(OpenWBBaseSensor):
    def __init__(self, dev_id, topic, key, initial_value, unit=None, icon=None):
        super().__init__(dev_id, topic, key, initial_value, unit, icon, devtype="chargepoint")

class OpenWBVehicleSensor(OpenWBBaseSensor):
    def __init__(self, dev_id, topic, key, initial_value, unit=None, icon=None):
        super().__init__(dev_id, topic, key, initial_value, unit, icon, devtype="vehicle")