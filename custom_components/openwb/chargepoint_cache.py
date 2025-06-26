import logging

_LOGGER = logging.getLogger(__name__)

_chargepoint_info_by_id: dict[int, dict] = {}

def update_chargepoint_info(chargepoint_id: int, name: str, manufacturer: str | None = None, model: str | None = None):
    _chargepoint_info_by_id[chargepoint_id] = {
        "name": name,
        "manufacturer": manufacturer,
        "model": model
    }
    _LOGGER.debug(f"Updated chargepoint cache: {chargepoint_id} → name='{name}', manufacturer='{manufacturer}', model='{model}'")

def get_chargepoint_info(chargepoint_id: int) -> dict | None:
    return _chargepoint_info_by_id.get(chargepoint_id)

def get_chargepoint_name(chargepoint_id: int) -> str | None:
    info = _chargepoint_info_by_id.get(chargepoint_id)
    return info.get("name") if info else None
