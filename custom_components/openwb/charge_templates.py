import logging
import json

from homeassistant.core import HomeAssistant
from homeassistant.components.number import NumberEntity
from homeassistant.components.text import TextEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.select import SelectEntity
from .charge_template_cache import get_charge_template, set_nested_value, update_charge_template, get_charge_template_name
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

def create_editable_entity(template_id: str, path: str, value):
    if _hass is None or _async_add_entities is None:
        _LOGGER.warning("Entitätsfactory noch nicht initialisiert: %s.%s", template_id, path)
        return

    config_key = path.replace(".", "/")
    config = CHARGE_TEMPLATE_CONFIG.get(config_key)
    if not config:
        _LOGGER.warning("Kein config-Eintrag für path: %s", path)
        return

    unique_id = f"openwb_charge_template_{template_id}_{path.replace('.', '_')}"
    friendly_name = f"openWB – Charge Template {template_id}: {config_key}"

    config_key = path.replace(".", "/")
    config = CHARGE_TEMPLATE_CONFIG.get(config_key, {})
    entity_type = config.get("type")

    # 💡 Priorisiere konfigurierten Typ
    if path == "id":
        _LOGGER.debug("Ignoriere nicht-editierbaren Pfad: %s", path)
        return
    elif entity_type == "switch":
        entity = ChargeTemplateSwitchEntity(_hass, template_id, path, value, friendly_name, unique_id)
    elif entity_type == "number":
        entity = ChargeTemplateNumberEntity(_hass, template_id, path, value, friendly_name, unique_id, config)
    elif entity_type == "select":
        entity = ChargeTemplateSelectEntity(_hass, template_id, path, str(value), friendly_name, unique_id, config)
    elif entity_type == "text" or isinstance(value, str):
        entity = ChargeTemplateTextEntity(_hass, template_id, path, value, friendly_name, unique_id)
    else:
        _LOGGER.warning(f"Unbekannter oder nicht unterstützter Typ für {path}: {type(value)}")
        return

    _async_add_entities([entity])
    _LOGGER.debug(f"Entität erfolgreich erstellt: {friendly_name}")

async def setup_entities_from_queue(hass: HomeAssistant):
    queued = drain_entity_queue()
    for entry in queued:
        entry_id, path, value = entry
        await create_editable_entity(hass, entry_id, path, value)

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
            "name": f"openWB – Charge Template {template_name} – (ID: {template_id})",
            "manufacturer": "openWB",
            "model": "Charge Template",
        }

    @property
    def current_option(self) -> str:
        return self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        if option not in self._attr_options:
            _LOGGER.warning("Ungültige Option '%s' für %s", option, self._attr_name)
            return
 
        from .charge_template_cache import get_charge_template, update_charge_template, set_nested_value

        template = get_charge_template(self._template_id)
        if not template:
            _LOGGER.warning("Template %s nicht gefunden", self._template_id)
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

class ChargeTemplateSwitchEntity(SwitchEntity):
    def __init__(self, hass, template_id, path, value, name, unique_id):
        self.hass = hass
        self._template_id = str(template_id)
        self._path = path
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_icon = "mdi:toggle-switch"
        self._attr_should_poll = False
        self._attr_is_on = bool(value)

    @property
    def is_on(self) -> bool:
        return self._attr_is_on

    async def async_turn_on(self, **kwargs) -> None:
        await self._update_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._update_state(False)

    async def _update_state(self, state: bool):
        from . import charge_template_cache
        from . import utils

        template = charge_template_cache.get_template(self._template_id)
        if not template:
            _LOGGER.warning("Template %s nicht gefunden", self._template_id)
            return

        utils.set_nested_value(template, self._path, state)
        charge_template_cache.update_charge_template(self._template_id, template)

        import json
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

        self._attr_is_on = state
        self.async_write_ha_state()


class ChargeTemplateTextEntity(ChargeTemplateBase, TextEntity):
    def __init__(self, hass, template_id, path, value, name, unique_id):
        ChargeTemplateBase.__init__(self, hass, template_id, path, value, name, unique_id)
        self._attr_native_value = value
        template_name = get_charge_template_name(str(template_id))
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"charge_template_{template_id}")},
            "name": f"openWB – Charge Template {template_name} – (ID: {template_id})",
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

        # Wende Konfiguration an, falls vorhanden
        self._attr_native_min_value = config.get("min", 0)
        self._attr_native_max_value = config.get("max", 1000)
        self._attr_native_step = config.get("step", 1)
        self._attr_native_unit_of_measurement = config.get("unit", None)
        template_name = get_charge_template_name(str(template_id))
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"charge_template_{template_id}")},
            "name": f"openWB – Charge Template {template_name} – (ID: {template_id})",
            "manufacturer": "openWB",
            "model": "Charge Template",
        }

    async def async_set_native_value(self, value):
        await self._update_and_publish(value)
        self._attr_native_value = value
        self.async_write_ha_state()


class ChargeTemplateSwitchEntity(ChargeTemplateBase, SwitchEntity):
    def __init__(self, hass, template_id, path, value, name, unique_id):
        ChargeTemplateBase.__init__(self, hass, template_id, path, value, name, unique_id)
        self._attr_is_on = value
        template_name = get_charge_template_name(str(template_id))
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"charge_template_{template_id}")},
            "name": f"openWB – Charge Template {template_name} – (ID: {template_id})",
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
