import logging
import json
from homeassistant.components.select import SelectEntity
from homeassistant.components.mqtt import async_publish
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from .const import DOMAIN, MQTT_PREFIX
from .cache.cache_template import get_all_charge_templates, get_template_id_by_name, get_charge_template_name, register_select_entity
from .cache.cache_vehicle import get_vehicle_info

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    from .charge_templates.entity_config import CHARGE_TEMPLATE_CONFIG
    from .charge_templates.entity_factory import create_editable_entity, drain_entity_queue_by_type, init_charge_template_entity_factory
    # Initialisiere Factory für generische charge_template-Entitäten
    init_charge_template_entity_factory(hass, async_add_entities)

    # ➤ Füge generische Select-Entitäten hinzu
    for template_id, path, value in drain_entity_queue_by_type("select"):
        config_key = path.replace(".", "/")
        entity_type = CHARGE_TEMPLATE_CONFIG.get(config_key, {}).get("type")

        if entity_type == "select":
            create_editable_entity(template_id, path, value)

    device_registry = async_get_device_registry(hass)
    entity_registry = async_get_entity_registry(hass)
    entities = []

    for device in device_registry.devices.values():
        related_entities = [
            e for e in entity_registry.entities.values()
            if e.device_id == device.id and e.domain == "sensor"
        ]
        if not related_entities:
            continue
    
        for ident in device.identifiers:
            if not isinstance(ident, tuple) or len(ident) != 2:
                continue
            domain, ident_str = ident
            if domain == DOMAIN and ident_str.startswith("openwb_vehicle_"):
                vehicle_id = ident_str.rsplit("_", 1)[-1]
                entities.append(OpenWBChargeTemplateSelector(vehicle_id))

    async_add_entities(entities)

class OpenWBChargeTemplateSelector(SelectEntity):
    def __init__(self, vehicle_id: str):
        self._vehicle_id = vehicle_id
        info = get_vehicle_info(int(vehicle_id))
        display_name = info.get("name") if info and info.get("name") else f"VEHICLE {vehicle_id}"

        self._attr_name = f"openWB - {display_name} - Charge Template Select"
        self._attr_unique_id = f"vehicle_{vehicle_id}_charge_template_select"
        self._attr_icon = "mdi:playlist-check"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"openwb_vehicle_{vehicle_id}")},
            "name": f"openWB - VEHICLE {vehicle_id}",
            "manufacturer": "openWB",
            "model": "MQTT",
        }

        info = get_vehicle_info(int(vehicle_id))
        current_template = None
        if info:
            template_id = str(info.get("charge_template"))
            _LOGGER.debug(f"Template ID pre-choise: {template_id}")
            current_template = get_charge_template_name(template_id)

        self._attr_current_option = current_template or "Template 0"

        register_select_entity(self)

    @property
    def options(self):
        templates = get_all_charge_templates().values()
        return list(templates) if templates else ["Template 0"]

    @property
    def current_option(self):
        return self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        template_id = get_template_id_by_name(option)
        if template_id is None:
            _LOGGER.warning(f"Template ID for '{option}' not found.")
            return
        topic = f"{MQTT_PREFIX}/set/vehicle/{self._vehicle_id}/charge_template"
        await async_publish(self.hass, topic, template_id, qos=0, retain=False)
        self._attr_current_option = option
        self.async_write_ha_state()

    def update_current_option_by_id(self, template_id: str):
        name = get_charge_template_name(template_id)
        if name:
            self._attr_current_option = name
            self.async_write_ha_state()
        else:
            _LOGGER.debug(f"Template name for ID {template_id} not yet in the cache. Wait for later update.")
    
    def get_template_id(self) -> str | None:
        info = get_vehicle_info(int(self._vehicle_id))
        return str(info.get("charge_template")) if info else None

