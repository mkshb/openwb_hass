import logging
from pprint import pformat

_LOGGER = logging.getLogger(__name__)

# Vollständige JSONs der Templates
_charge_template_data_by_id = {}
_ev_template_name_by_id = {}

SELECT_ENTITIES: list = []
NUMBER_ENTITIES: list = []
SWITCH_ENTITIES: list = []

def register_select_entity(entity):
    _LOGGER.debug("📌 SelectEntity registriert: %s (%s)", getattr(entity, "name", repr(entity)), entity.__class__.__name__)
    SELECT_ENTITIES.append(entity)

def register_number_entity(entity):
    _LOGGER.debug("📌 NumberEntity registriert: %s (%s)", getattr(entity, "name", repr(entity)), entity.__class__.__name__)
    NUMBER_ENTITIES.append(entity)

def register_switch_entity(entity):
    _LOGGER.debug("📌 SwitchEntity registriert: %s (%s)", getattr(entity, "name", repr(entity)), entity.__class__.__name__)
    SWITCH_ENTITIES.append(entity)    

def update_charge_template(template_id: str, data: dict):
    _charge_template_data_by_id[template_id] = data
    _LOGGER.debug("update_charge_template() aufgerufen für ID %s", template_id)
    name = data.get("name")
    if name:
        update_charge_template_name(template_id, name)

    #_LOGGER.debug("SWITCH_ENTITIES beim update_charge_template: %s", SWITCH_ENTITIES)
    #_LOGGER.debug("Anzahl SWITCH_ENTITIES: %d", len(SWITCH_ENTITIES))

    from .select import OpenWBChargeTemplateSelector
    from .charge_templates import ChargeTemplateNumberEntity, ChargeTemplateSwitchEntity
    
    for entity in SELECT_ENTITIES:
        if isinstance(entity, OpenWBChargeTemplateSelector):
            if entity.get_template_id() == str(template_id):
                _LOGGER.debug("✔ Selector für Vehicle aktualisieren: %s", entity)
                entity.update_current_option_by_id(str(template_id))
        elif hasattr(entity, "get_template_id") and entity.get_template_id() == str(template_id):
            if hasattr(entity, "update_value_from_cache"):
                _LOGGER.debug("→ update_value_from_cache wird aufgerufen für: %s", entity)
                entity.update_value_from_cache()

    for entity in NUMBER_ENTITIES:
        if isinstance(entity, ChargeTemplateNumberEntity):
            if str(entity._template_id) == str(template_id):
                _LOGGER.debug("🔢 Aktualisiere NumberEntity: %s", entity.name)
                entity.update_value_from_cache()

    for entity in SWITCH_ENTITIES:
        if isinstance(entity, ChargeTemplateSwitchEntity):
            if str(entity._template_id) == str(template_id):
                _LOGGER.debug("🔢 Aktualisiere SwitchEntity: %s", entity.name)
                entity.update_value_from_cache()
    

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
        if hasattr(selector, "get_template_id") and selector.get_template_id() == template_id:
            if hasattr(selector, "update_current_option_by_id"):
                selector.update_current_option_by_id(template_id)
            else:
                _LOGGER.debug("⛔ Entität ohne update_current_option_by_id(): %s (%s)", selector.name, selector.__class__.__name__)


def get_all_charge_templates():
    _LOGGER.debug(f"Templates in cache: {get_all_template_names()}")
    return get_all_template_names()

def get_all_ev_templates() -> dict:
    return _ev_template_name_by_id.copy()

def update_ev_template_name(template_id: str, name: str):
    _ev_template_name_by_id[template_id] = name

def get_ev_template_name(template_id: str) -> str | None:
    return _ev_template_name_by_id.get(template_id)
