import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .charge_templates import drain_entity_queue_by_type, init_charge_template_entity_factory

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

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    from .charge_template_entity_config import CHARGE_TEMPLATE_CONFIG
    from .charge_templates import create_editable_entity

    init_charge_template_entity_factory(hass, async_add_entities)

    for template_id, path, value in drain_entity_queue_by_type("switch"):
        config_key = path.replace(".", "/")
        entity_type = CHARGE_TEMPLATE_CONFIG.get(config_key, {}).get("type")

        if entity_type == "switch":
            create_editable_entity(template_id, path, value)

    return True
