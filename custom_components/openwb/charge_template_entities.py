import json
import logging
from homeassistant.components.number import NumberEntity
from homeassistant.components.text import TextEntity
from homeassistant.components.switch import SwitchEntity
from .charge_template_cache import get_charge_template, set_nested_value, update_charge_template

_LOGGER = logging.getLogger(__name__)


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


class ChargeTemplateTextEntity(ChargeTemplateBase, TextEntity):
    def __init__(self, hass, template_id, path, value, name, unique_id):
        super().__init__(hass, template_id, path, value, name, unique_id)
        self._attr_native_value = value

    async def async_set_value(self, value: str):
        await self._update_and_publish(value)
        self._attr_native_value = value
        self.async_write_ha_state()


class ChargeTemplateNumberEntity(ChargeTemplateBase, NumberEntity):
    def __init__(self, hass, template_id, path, value, name, unique_id):
        super().__init__(hass, template_id, path, value, name, unique_id)
        self._attr_native_value = value
        self._attr_min_value = 0
        self._attr_max_value = 50000
        self._attr_step = 1
        if isinstance(value, float):
            self._attr_step = 0.1

    async def async_set_native_value(self, value):
        await self._update_and_publish(value)
        self._attr_native_value = value
        self.async_write_ha_state()


class ChargeTemplateSwitchEntity(ChargeTemplateBase, SwitchEntity):
    def __init__(self, hass, template_id, path, value, name, unique_id):
        super().__init__(hass, template_id, path, value, name, unique_id)
        self._attr_is_on = value

    async def async_turn_on(self, **kwargs):
        await self._update_and_publish(True)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self._update_and_publish(False)
        self._attr_is_on = False
        self.async_write_ha_state()
