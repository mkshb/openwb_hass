import logging

_LOGGER = logging.getLogger(__name__)

_chargepoint_info_by_id: dict[int, dict] = {}

_cache = {}

_cache = {}

def update_chargepoint_info(dev_id: int, config: dict):
    name = config.get("name", f"Chargepoint {dev_id}")
    manufacturer = config.get("manufacturer", "openWB")
    model = config.get("type", "openWB Chargepoint")

    _cache[dev_id] = {
        "name": name,
        "manufacturer": manufacturer,
        "model": model
    }

def get_chargepoint_info(dev_id: int) -> dict | None:
    return _cache.get(dev_id)

def get_chargepoint_name(chargepoint_id: int) -> str | None:
    info = _chargepoint_info_by_id.get(chargepoint_id)
    return info.get("name") if info else None
