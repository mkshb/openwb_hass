import logging

_LOGGER = logging.getLogger(__name__)

_ev_template_name_by_id = {}

def update_ev_template_name(template_id: str, name: str):
    _ev_template_name_by_id[template_id] = name
    _LOGGER.debug("EV-Template-Name gesetzt: %s = %s", template_id, name)

def get_ev_template_name(template_id: str) -> str | None:
    return _ev_template_name_by_id.get(template_id)

def get_all_ev_templates() -> dict:
    return _ev_template_name_by_id.copy()

def delete_ev_template(template_id: str):
    _ev_template_name_by_id.pop(template_id, None)

def ev_template_exists(template_id: str) -> bool:
    return template_id in _ev_template_name_by_id
