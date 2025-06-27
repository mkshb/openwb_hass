import logging
from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MQTT_PREFIX
from .charge_template_cache import update_charge_template
from .charge_template_entity_config import CHARGE_TEMPLATE_CONFIG
from .mqtt import send_mqtt_message
from .charge_templates import drain_entity_queue_by_type, init_charge_template_entity_factory
from .charge_template_cache import register_number_entity

_LOGGER = logging.getLogger(__name__)

class OpenWBChargeTemplateNumber(NumberEntity):
    def __init__(self, template_id, path, value, config):
        self._template_id = str(template_id)
        self._path = path
        self._state = float(value)
        self._min = config.get("min", 0)
        self._max = config.get("max", 100)
        self._step = config.get("step", 1)
        self._unit = config.get("unit", None)
        self._icon = config.get("icon", "mdi:ray-start")
 
        key = path.replace(".", "_")
        self._attr_unique_id = f"openwb_template_{self._template_id}_{key}"
        self._attr_name = f"openWB Template {self._template_id} – {key.replace('_', ' ').title()}"
        self._attr_native_min_value = self._min
        self._attr_native_max_value = self._max
        self._attr_native_step = self._step
        self._attr_native_unit_of_measurement = self._unit
        self._attr_icon = self._icon
        self._attr_should_poll = False

        register_number_entity(self)

    @property
    def native_value(self):
        return self._state

    async def async_set_native_value(self, value: float):
        self._state = value
        await self._update_template_value(value)
        self.async_write_ha_state()

    async def _update_template_value(self, value):
        try:
            from .charge_template_cache import get_template
            template = get_template(self._template_id)
            if template is None:
                _LOGGER.warning(f"Template {self._template_id} not found")
                return

            parts = self._path.split(".")
            d = template
            for part in parts[:-1]:
                d = d.setdefault(part, {})
            d[parts[-1]] = value

            update_charge_template(self._template_id, template)
            topic = f"{MQTT_PREFIX}/set/vehicle/template/charge_template/{self._template_id}"
            await send_mqtt_message(topic, template)

            _LOGGER.debug(f"Template {self._template_id} – {self._path} set to {value} and published")

        except Exception as e:
            _LOGGER.warning(f"Error when updating {self._path} in template {self._template_id}: {e}")
    
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

        if value is not None and float(value) != self._state:
            _LOGGER.debug("🔄 Update Number %s: %s -> %s", self._attr_name, self._state, value)
            self._state = float(value)
            self.async_write_ha_state()

async def async_setup_entry(hass, entry, async_add_entities):
    init_charge_template_entity_factory(hass, async_add_entities)

    # Jetzt alle Entities abholen, die zu dieser Plattform passen
    entities = []
    for template_id, path, value in drain_entity_queue_by_type("number"):
        # Filter anhand deiner Plattform
        from .charge_template_entity_config import CHARGE_TEMPLATE_CONFIG
        config_key = path.replace(".", "/")
        entity_type = CHARGE_TEMPLATE_CONFIG.get(config_key, {}).get("type")

        if entity_type == "number":  # <- Datei für number.py
            from .charge_templates import create_editable_entity
            create_editable_entity(template_id, path, value)

    return True


