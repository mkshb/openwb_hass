import logging
import json
from pprint import pformat

_LOGGER = logging.getLogger(__name__)

_charge_template_data_by_id = {}

SELECT_ENTITIES: list = []
NUMBER_ENTITIES: list = []
SWITCH_ENTITIES: list = []

_registered_entities = []

def register_entity(entity):
    _registered_entities.append(entity)

def get_registered_entities():
    return _registered_entities

def register_select_entity(entity):
    _LOGGER.debug("SelectEntity registriert: %s (%s)", getattr(entity, "name", repr(entity)), entity.__class__.__name__)
    SELECT_ENTITIES.append(entity)

def register_number_entity(entity):
    _LOGGER.debug("NumberEntity registriert: %s (%s)", getattr(entity, "name", repr(entity)), entity.__class__.__name__)
    NUMBER_ENTITIES.append(entity)

def register_switch_entity(entity):
    _LOGGER.debug("SwitchEntity registriert: %s (%s)", getattr(entity, "name", repr(entity)), entity.__class__.__name__)
    SWITCH_ENTITIES.append(entity)

def update_charge_template(template_id: str, data: dict):
    _charge_template_data_by_id[template_id] = data
    _LOGGER.debug("New data for template %s:\n%s", template_id, json.dumps(data, indent=2))
    name = data.get("name")
    if name:
        update_charge_template_name(template_id, name)

    from ..charge_templates.entity_factory import ChargeTemplateNumberEntity, ChargeTemplateSwitchEntity, ChargeTemplateSelectEntity

   
    for entity in SELECT_ENTITIES:
        _LOGGER.debug("Geprüfte Entity: %s – Template-ID: %s", entity.name, entity.get_template_id())
        if hasattr(entity, "get_template_id") and entity.get_template_id() == str(template_id):
            if hasattr(entity, "update_value_from_cache"):
                _LOGGER.debug("→ update_value_from_cache für: %s", entity)
                entity.update_value_from_cache()    

    for entity in NUMBER_ENTITIES:
        if isinstance(entity, ChargeTemplateNumberEntity) and str(entity._template_id) == str(template_id):
            _LOGGER.debug("\ud83d\udd22 Aktualisiere NumberEntity: %s", entity.name)
            entity.update_value_from_cache()

    for entity in SWITCH_ENTITIES:
        if isinstance(entity, ChargeTemplateSwitchEntity) and str(entity._template_id) == str(template_id):
            _LOGGER.debug("\ud83d\udd18 Aktualisiere SwitchEntity: %s", entity.name)
            entity.update_value_from_cache()

def get_charge_template(template_id: str) -> dict:
    return _charge_template_data_by_id.get(template_id, {})

def update_charge_template_name(template_id: str, name: str):
    template = _charge_template_data_by_id.setdefault(template_id, {})
    template["name"] = name

    for selector in SELECT_ENTITIES:
        if hasattr(selector, "get_template_id") and selector.get_template_id() == template_id:
            if hasattr(selector, "update_current_option_by_id"):
                selector.update_current_option_by_id(template_id)
            else:
                _LOGGER.debug("Entit\u00e4t ohne update_current_option_by_id(): %s (%s)", selector.name, selector.__class__.__name__)

def get_charge_template_name(template_id: str) -> str | None:
    template = _charge_template_data_by_id.get(template_id)
    return template.get("name") if template else None

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

def get_all_templates():
    return _charge_template_data_by_id.copy()

def template_exists(template_id: str) -> bool:
    return template_id in _charge_template_data_by_id

def delete_template(template_id: str):
    _charge_template_data_by_id.pop(template_id, None)

def log_all_templates():
    _LOGGER.info("Aktuelle Charge Templates:\n%s", pformat(_charge_template_data_by_id))

def set_nested_value(d, path: str, value):
    keys = path.split(".")
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value
