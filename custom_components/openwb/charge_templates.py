import logging
import json
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.components.number import NumberEntity
from homeassistant.components.text import TextEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.select import SelectEntity
from .charge_template_cache import get_charge_template, set_nested_value, update_charge_template, get_charge_template_name, register_select_entity, register_number_entity, register_switch_entity
from .charge_template_entity_config import CHARGE_TEMPLATE_CONFIG
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_hass = None
_async_add_entities = None

def init_charge_template_entity_factory(hass, async_add_entities):
    global _hass, _async_add_entities
    _hass = hass
    _async_add_entities = async_add_entities

_entity_queue = []

def queue_entity(template_id: str, path: str, value):
    _entity_queue.append((template_id, path, value))

def drain_entity_queue():
    queued = list(_entity_queue)
    _entity_queue.clear()
    return queued

def drain_entity_queue_by_type(entity_type: str):
    matches = []
    rest = []

    for entry in _entity_queue:
        template_id, path, value = entry
        config_key = path.replace(".", "/")
        type_in_config = CHARGE_TEMPLATE_CONFIG.get(config_key, {}).get("type")
        if type_in_config == entity_type:
            matches.append(entry)
        else:
            rest.append(entry)

    _entity_queue.clear()
    _entity_queue.extend(rest)
    return matches

class ChargeTemplateBase:
    def __init__(self, hass, template_id, path, value, name, unique_id):
        self.hass = hass
        self._template_id = template_id
        self._path = path
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._value = value

    async def _update_and_publish(self, value):
        template = get_charge_template(self._template_id)
        set_nested_value(template, self._path, value)
        update_charge_template(self._template_id, template)

        topic = f"openWB/set/vehicle/template/charge_template/{self._template_id}"
        payload = json.dumps(template)
       
        await self.hass.services.async_call(
            "mqtt",
            "publish",
            {
                "topic": topic,
                "payload": payload,
                "qos": 0,
                "retain": False,
            },
            blocking=True,
        )

class ChargeTemplateSelectEntity(SelectEntity):
    def __init__(self, hass, template_id, path, value, name, unique_id, config):
        self.hass = hass
        self._template_id = str(template_id)
        self._path = path
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_icon = "mdi:form-select"
        self._attr_should_poll = False

        self._attr_options = [str(opt) for opt in config.get("options", [])]
        self._attr_current_option = str(value)
        template_name = get_charge_template_name(str(template_id))
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"charge_template_{template_id}")},
            "name": f"openWB – Charge Template – {template_name} (ID: {template_id})",
            "manufacturer": "openWB",
            "model": "Charge Template",
        }

    @property
    def current_option(self) -> str:
        return self._attr_current_option
    
    def get_template_id(self) -> str:
        return self._template_id

    def update_value_from_cache(self):
        from .charge_template_cache import get_charge_template

        # Lese verschachtelten Wert neu aus dem Cache
        template = get_charge_template(self._template_id)
        value = template
        for key in self._path.split("."):
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
                break

        if value is not None and str(value) != self._attr_current_option:
            _LOGGER.debug("Update %s: %s -> %s", self._attr_name, self._attr_current_option, value)
            self._attr_current_option = str(value)

            # 👉 async_write_ha_state asynchron ausführen
            self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        if option not in self._attr_options:
            _LOGGER.warning("Ungültige Option '%s' für %s", option, self._attr_name)
            return
 
        from .charge_template_cache import get_charge_template, update_charge_template, set_nested_value

        await asyncio.sleep(0.1)
        template = get_charge_template(self._template_id)
        if not template:
            _LOGGER.warning("Template %s not found", self._template_id)
            return

        set_nested_value(template, self._path, option)
        update_charge_template(self._template_id, template)

        topic = f"openWB/set/vehicle/template/charge_template/{self._template_id}"
        payload = json.dumps(template)

        _LOGGER.debug("Publishing updated template %s: %s", self._template_id, payload)

        await self.hass.services.async_call(
            "mqtt",
            "publish",
            {
                "topic": topic,
                "payload": payload,
                "qos": 0,
                "retain": False,
            },
            blocking=True,
        )

        self._attr_current_option = option
        self.async_write_ha_state()

class ChargeTemplateTextEntity(ChargeTemplateBase, TextEntity):
    def __init__(self, hass, template_id, path, value, name, unique_id):
        ChargeTemplateBase.__init__(self, hass, template_id, path, value, name, unique_id)
        self._attr_native_value = value
        template_name = get_charge_template_name(str(template_id))
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"charge_template_{template_id}")},
            "name": f"openWB – Charge Template – {template_name} (ID: {template_id})",
            "manufacturer": "openWB",
            "model": "Charge Template",
        }

    async def async_set_value(self, value: str):
        await self._update_and_publish(value)
        self._attr_native_value = value
        self.async_write_ha_state()


class ChargeTemplateNumberEntity(ChargeTemplateBase, NumberEntity):
    def __init__(self, hass, template_id, path, value, name, unique_id, config=None):
        ChargeTemplateBase.__init__(self, hass, template_id, path, value, name, unique_id)
        self._attr_native_value = value
        self._attr_name = name
        self._attr_native_min_value = config.get("min", 0)
        self._attr_native_max_value = config.get("max", 1000)
        self._attr_native_step = config.get("step", 1)
        self._attr_native_unit_of_measurement = config.get("unit", None)
        template_name = get_charge_template_name(str(template_id))
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"charge_template_{template_id}")},
            "name": f"openWB – Charge Template – {template_name} (ID: {template_id})",
            "manufacturer": "openWB",
            "model": "Charge Template",
        }

    async def async_set_native_value(self, value):
        await self._update_and_publish(value)
        self._attr_native_value = value
        self.async_write_ha_state()

    def update_value_from_cache(self):
        from .charge_template_cache import get_charge_template
    
        template = get_charge_template(self._template_id)
        value = template
        for key in self._path.split("."):
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
                break
    
        if value is not None and value != self._attr_native_value:
            _LOGGER.debug("🔢 Update %s: %s -> %s", self._attr_name, self._attr_native_value, value)
            self._attr_native_value = value
            self.async_write_ha_state()
        else:
            _LOGGER.debug("🔢 Kein Update nötig: %s bleibt bei %s", self._attr_name, self._attr_native_value)
    
class ChargeTemplateSwitchEntity(ChargeTemplateBase, SwitchEntity):
    def __init__(self, hass, template_id, path, value, name, unique_id):
        ChargeTemplateBase.__init__(self, hass, template_id, path, value, name, unique_id)
        self._attr_is_on = value
        template_name = get_charge_template_name(str(template_id))
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"charge_template_{template_id}")},
            "name": f"openWB – Charge Template – {template_name} (ID: {template_id})",
            "manufacturer": "openWB",
            "model": "Charge Template",
        }

    async def async_turn_on(self, **kwargs):
        await self._update_and_publish(True)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self._update_and_publish(False)
        self._attr_is_on = False
        self.async_write_ha_state()

    def update_value_from_cache(self):
        from .charge_template_cache import get_charge_template
    
        template = get_charge_template(self._template_id)
        value = template
        for key in self._path.split("."):
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
                break
    
        if isinstance(value, bool) and value != self._attr_is_on:
            _LOGGER.debug("🔢 Update Switch %s: %s -> %s", self._attr_name, self._attr_is_on, value)
            self._attr_is_on = value
            self.async_write_ha_state()
        else:
            _LOGGER.debug("🔢 Kein Update nötig für %s: bleibt bei %s", self._attr_name, self._attr_is_on)
    

def create_editable_entity(template_id: str, path: str, value):
    if _hass is None or _async_add_entities is None:
        _LOGGER.warning("Entity factory not yet initialized: %s.%s", template_id, path)
        return

    config_key = path.replace(".", "/")
    config = CHARGE_TEMPLATE_CONFIG.get(config_key)
    if not config:
        _LOGGER.warning("No config entry for path: %s", path)
        return

    unique_id = f"openwb_charge_template_{template_id}_{path.replace('.', '_')}"
    friendly_name = f"openWB – Charge Template {template_id}: {config_key}"

    config_key = path.replace(".", "/")
    config = CHARGE_TEMPLATE_CONFIG.get(config_key, {})
    entity_type = config.get("type")

    # 💡 Priorisiere konfigurierten Typ
    if path == "id":
        _LOGGER.debug("Ignore non-editable path: %s", path)
        return
    elif entity_type == "switch":
        entity = ChargeTemplateSwitchEntity(_hass, template_id, path, value, friendly_name, unique_id)
        register_switch_entity(entity)
    elif entity_type == "number":
        entity = ChargeTemplateNumberEntity(_hass, template_id, path, value, friendly_name, unique_id, config)
        register_number_entity(entity)
    elif entity_type == "select":
        entity = ChargeTemplateSelectEntity(_hass, template_id, path, str(value), friendly_name, unique_id, config)
        register_select_entity(entity)
    elif entity_type == "text" or isinstance(value, str):
        entity = ChargeTemplateTextEntity(_hass, template_id, path, value, friendly_name, unique_id)
    else:
        _LOGGER.warning(f"Unknown or unsupported type for {path}: {type(value)}")
        return

    _async_add_entities([entity])
    _LOGGER.debug(f"Entity successfully created: {friendly_name}")

async def setup_entities_from_queue(hass: HomeAssistant):
    queued = drain_entity_queue()
    for entry in queued:
        entry_id, path, value = entry
        await create_editable_entity(hass, entry_id, path, value)