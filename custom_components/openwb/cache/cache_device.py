import logging

_LOGGER = logging.getLogger(__name__)

_MQTT_TYPE_TO_CONFIG_TYPE = {
    "counter": "counter",
    "pv": "inverter",  # wichtig: pv → inverter
    "bat": "bat",
    "vehicle": "vehicle",
    "chargepoint": "chargepoint",
}

_device_info_by_type_and_id: dict[tuple[str, int], dict] = {}

def update_device_name(device_type: str, device_id: int, name: str, manufacturer: str | None = None, model: str | None = None):
    key = (device_type, device_id)
    _device_info_by_type_and_id[key] = {
        "name": name,
        "manufacturer": manufacturer,
        "model": model
    }
    _LOGGER.debug(f"Updated device cache: {key} → name='{name}', manufacturer='{manufacturer}', model='{model}'")

def get_device_name(mqtt_type: str, device_id: int) -> str | None:
    config_type = _MQTT_TYPE_TO_CONFIG_TYPE.get(mqtt_type, mqtt_type)
    info = _device_info_by_type_and_id.get((config_type, device_id))
    return info.get("name") if info else None

def get_device_info(device_type: str, device_id: int) -> dict | None:
    return _device_info_by_type_and_id.get((device_type, device_id))

def get_all_device_infos() -> dict[tuple[str, int], dict]:
    return _device_info_by_type_and_id.copy()
