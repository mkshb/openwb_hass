import logging
from homeassistant.components.select import SelectEntity
from homeassistant.components.mqtt import async_publish
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from .const import DOMAIN, MQTT_PREFIX
from .template_cache import get_all_charge_templates, get_template_id_by_name, get_charge_template_name


_LOGGER = logging.getLogger(__name__)

SELECT_ENTITIES: list["OpenWBChargeTemplateSelector"] = []

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):

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
        self._attr_current_option = None
        self._attr_name = f"Vehicle {vehicle_id} Charge Template Select"
        self._attr_unique_id = f"vehicle_{vehicle_id}_charge_template_select"
        self._attr_icon = "mdi:playlist-check"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"openwb_vehicle_{vehicle_id}")},
            "name": f"openWB - VEHICLE {vehicle_id}",
            "manufacturer": "openWB",
            "model": "MQTT",
        }

        SELECT_ENTITIES.append(self)

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
            _LOGGER.warning(f"Template-ID für '{option}' nicht gefunden.")
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
