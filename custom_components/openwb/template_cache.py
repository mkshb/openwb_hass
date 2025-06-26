import logging

_LOGGER = logging.getLogger(__name__)

_charge_template_name_by_id = {}
_ev_template_name_by_id = {}

def update_charge_template_name(template_id: str, name: str):
    _charge_template_name_by_id[template_id] = name

    from .select import SELECT_ENTITIES
    for selector in SELECT_ENTITIES:
        if selector.get_template_id() == template_id:
            selector.update_current_option_by_id(template_id)

def update_ev_template_name(template_id: str, name: str):
    _ev_template_name_by_id[template_id] = name

def get_charge_template_name(template_id: str) -> str | None:
    return _charge_template_name_by_id.get(template_id)

def get_ev_template_name(template_id: str) -> str | None:
    return _ev_template_name_by_id.get(template_id)

def get_all_charge_templates():
    _LOGGER.debug(f"Templates in cache: {_charge_template_name_by_id}")
    return _charge_template_name_by_id.copy()

def get_all_ev_templates() -> dict:
    return _ev_template_name_by_id.copy()

def get_template_id_by_name(name: str) -> str | None:
    for tid, n in _charge_template_name_by_id.items():
        if n == name:
            return tid
    return None