import asyncio
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .mqtt_device_info_handler import subscribe_to_device_configs
from .mqtt_vehicle_info_handler import subscribe_to_vehicle_info
from .mqtt_chargepoint_info_handler import subscribe_to_chargepoint_info
from .mqtt_charge_template_handler import subscribe_to_charge_templates



DOMAIN = "openwb"
PLATFORMS = ["sensor", "number", "select", "switch", "text"]

async def async_setup(hass: HomeAssistant, config: ConfigType):
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    mqtt_client = hass.data["mqtt"].client
    subscribe_to_vehicle_info(mqtt_client)
    subscribe_to_device_configs(mqtt_client)
    subscribe_to_chargepoint_info(mqtt_client)
    subscribe_to_charge_templates(mqtt_client)

    await asyncio.sleep(2)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    results = await asyncio.gather(
        *[hass.config_entries.async_forward_entry_unload(entry, platform) for platform in PLATFORMS]
    )
    return all(results)