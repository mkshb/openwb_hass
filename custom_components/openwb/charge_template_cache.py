import logging
from pprint import pformat

_LOGGER = logging.getLogger(__name__)

# Vollständige JSONs der Templates
_charge_template_data_by_id = {}
_ev_template_name_by_id = {}

SELECT_ENTITIES: list = []  # Wird extern überschrieben

def update_charge_template(template_id: str, data: dict):
    _charge_template_data_by_id[template_id] = data
    name = data.get("name")
    if name:
        update_charge_template_name(template_id, name)

def get_charge_template(template_id: str) -> dict:
    return _charge_template_data_by_id.get(template_id, {})

def set_nested_value(d, path: str, value):
    keys = path.split(".")
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value

def get_all_templates():
    return _charge_template_data_by_id.copy()

def get_charge_template_name(template_id: str) -> str | None:
    template = _charge_template_data_by_id.get(template_id)
    if template:
        return template.get("name")
    return None

def get_template_id_by_name(name: str) -> str | None:
    for tid, template in _charge_template_data_by_id.items():
        if template.get("name") == name:
            return tid
    return None

def get_all_template_names() -> dict:
    return {
        tid: template.get("name", f"Template {tid}")
        for tid, template in _charge_template_data_by_id.items()
    }

def template_exists(template_id: str) -> bool:
    return template_id in _charge_template_data_by_id

def delete_template(template_id: str):
    if template_id in _charge_template_data_by_id:
        del _charge_template_data_by_id[template_id]

def log_all_templates():
    _LOGGER.info("Aktuelle Charge Templates:\n%s", pformat(_charge_template_data_by_id))

def update_charge_template_name(template_id: str, name: str):
    template = _charge_template_data_by_id.setdefault(template_id, {})
    template["name"] = name
    for selector in SELECT_ENTITIES:
        if selector.get_template_id() == template_id:
            selector.update_current_option_by_id(template_id)

def get_all_charge_templates():
    _LOGGER.debug(f"Templates in cache: {get_all_template_names()}")
    return get_all_template_names()

def get_all_ev_templates() -> dict:
    return _ev_template_name_by_id.copy()

def update_ev_template_name(template_id: str, name: str):
    _ev_template_name_by_id[template_id] = name

def get_ev_template_name(template_id: str) -> str | None:
    return _ev_template_name_by_id.get(template_id)
