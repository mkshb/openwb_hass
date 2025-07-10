import logging

_LOGGER = logging.getLogger(__name__)

_vehicle_data: dict[int, dict] = {}

def clean(value):
    if isinstance(value, str):
        return value.strip('"') 
    return value

def update_vehicle_info(vehicle_id: int | str, **kwargs):
    try:
        vehicle_id = int(vehicle_id)
    except (ValueError, TypeError):
        _LOGGER.warning(f"Ignore invalid vehicle_id={vehicle_id}")
        return

    info = _vehicle_data.setdefault(vehicle_id, {})
    for key, value in kwargs.items():
        if value is not None:
            info[key] = clean(value)

    _LOGGER.debug(f"Updated vehicle cache [{vehicle_id}]: {info}")

def update_vehicle_templates(vehicle_id: int | str, key: str, value):
    try:
        vehicle_id = int(vehicle_id)
    except (ValueError, TypeError):
        _LOGGER.warning(f"Ignore invalid vehicle_id={vehicle_id}")
        return

    info = _vehicle_data.setdefault(vehicle_id, {})
    info[key] = value
    _LOGGER.debug(f"Updated vehicle cache: {vehicle_id} → {key} = {value}")

def get_vehicle_info(vehicle_id: int) -> dict:
    return _vehicle_data.get(vehicle_id, {})

def get_all_vehicle_infos() -> dict[int, dict]:
    return _vehicle_data.copy()

def log_vehicle_cache():
    for vid, data in _vehicle_data.items():
        _LOGGER.warning(f"Vehicle {vid}: {data}")