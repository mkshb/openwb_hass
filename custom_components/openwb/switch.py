import logging
import asyncio

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .charge_templates.entity_factory import drain_entity_queue_by_type, init_charge_template_entity_factory
from .cache.cache_template import register_switch_entity

_LOGGER = logging.getLogger(__name__)

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

        register_switch_entity(self)

    @property
    def is_on(self) -> bool:
        return self._attr_is_on

    async def async_turn_on(self, **kwargs) -> None:
        await self._update_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._update_state(False)

    async def _update_state(self, state: bool):
        from . import cache_template
        from . import utils

        await asyncio.sleep(0.1)
        template = cache_template.get_template(self._template_id)
        if not template:
            _LOGGER.warning("Template %s not found", self._template_id)
            return

        utils.set_nested_value(template, self._path, state)
        cache_template.update_charge_template(self._template_id, template)

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

    def update_value_from_cache(self):
        from .cache_template import get_template
    
        template = get_template(self._template_id)
        value = template
        for key in self._path.split("."):
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
                break
    
        if isinstance(value, bool) and value != self._attr_is_on:
            _LOGGER.warning("🔄 Update Switch %s: %s -> %s", self.name, self._attr_is_on, value)
            self._attr_is_on = value
            self.async_write_ha_state()
        

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    from .charge_templates.entity_config import CHARGE_TEMPLATE_CONFIG
    from .charge_templates.entity_factory import create_editable_entity

    init_charge_template_entity_factory(hass, async_add_entities)

    for template_id, path, value in drain_entity_queue_by_type("switch"):
        config_key = path.replace(".", "/")
        entity_type = CHARGE_TEMPLATE_CONFIG.get(config_key, {}).get("type")

        if entity_type == "switch":
            create_editable_entity(template_id, path, value)

    return True
