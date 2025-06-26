import logging

_LOGGER = logging.getLogger(__name__)

_vehicle_data: dict[int, dict] = {}

def update_vehicle_info(vehicle_id: int | str, name: str | None = None, manufacturer: str | None = None, model: str | None = None):
    try:
        vehicle_id = int(vehicle_id)
    except (ValueError, TypeError):
        _LOGGER.warning(f"Ignoriere ungültige vehicle_id={vehicle_id} (nicht konvertierbar in int)")
        return

    info = _vehicle_data.setdefault(vehicle_id, {})
    if name is not None:
        info["name"] = name
    if manufacturer is not None:
        info["manufacturer"] = manufacturer
    if model is not None:
        info["model"] = model
    _LOGGER.warning(f"Updated vehicle cache: {vehicle_id} → name='{info.get('name')}', manufacturer='{info.get('manufacturer')}', model='{info.get('model')}'")

def update_vehicle_templates(vehicle_id: int | str, key: str, value):
    try:
        vehicle_id = int(vehicle_id)
    except (ValueError, TypeError):
        _LOGGER.warning(f"Ignoriere ungültige vehicle_id={vehicle_id} (nicht konvertierbar in int)")
        return

    info = _vehicle_data.setdefault(vehicle_id, {})
    info[key] = value
    _LOGGER.debug(f"Updated vehicle cache: {vehicle_id} → {key} = {value}")

def get_vehicle_info(vehicle_id: int) -> dict | None:
    return _vehicle_data.get(vehicle_id)

def get_all_vehicle_infos() -> dict[int, dict]:
    return _vehicle_data.copy()