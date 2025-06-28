import logging

_LOGGER = logging.getLogger(__name__)

_bat_data: dict[int, dict] = {}

def clean(value):
    if isinstance(value, str):
        return value.strip('"') 
    return value

def update_bat_info(bat_id: int | str, **kwargs):
    try:
        bat_id = int(bat_id)
    except (ValueError, TypeError):
        _LOGGER.warning(f"Ignore invalid bat_id={bat_id}")
        return

    info = _bat_data.setdefault(bat_id, {})
    for key, value in kwargs.items():
        if value is not None:
            info[key] = clean(value)

    _LOGGER.debug(f"Updated battery cache [{bat_id}]: {info}")

def update_bat_attribute(bat_id: int | str, key: str, value):
    try:
        bat_id = int(bat_id)
    except (ValueError, TypeError):
        _LOGGER.warning(f"Ignore invalid bat_id={bat_id}")
        return

    info = _bat_data.setdefault(bat_id, {})
    info[key] = clean(value)
    _LOGGER.debug(f"Updated battery cache: {bat_id} → {key} = {value}")

def get_bat_info(bat_id: int) -> dict:
    return _bat_data.get(bat_id, {})

def get_all_bat_infos() -> dict[int, dict]:
    return _bat_data.copy()

def log_bat_cache():
    for bid, data in _bat_data.items():
        _LOGGER.warning(f"Battery {bid}: {data}")
