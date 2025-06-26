import logging

_LOGGER = logging.getLogger(__name__)

# Vollständige JSONs der Templates
_charge_template_data_by_id = {}


def update_charge_template(template_id: str, data: dict):
    _charge_template_data_by_id[template_id] = data


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

def template_exists(template_id: str) -> bool:
    return template_id in _charge_template_data_by_id


def log_all_templates():
    from pprint import pformat
    _LOGGER.info("Current charge templates:\n%s", pformat(_charge_template_data_by_id))