import json
import logging
import custom_components.openwb.charge_template_cache as charge_template_cache
from .utils import flatten_json
from .charge_templates import queue_entity, CHARGE_TEMPLATE_CONFIG


_LOGGER = logging.getLogger(__name__)

CHARGE_TEMPLATE_TOPIC_PATTERN = "openWB/vehicle/template/charge_template/+"

def subscribe_to_charge_templates(mqtt_client):
    mqtt_client.async_subscribe(CHARGE_TEMPLATE_TOPIC_PATTERN, _handle_charge_template_topic, 0)
    _LOGGER.debug(f"Subscribed to: {CHARGE_TEMPLATE_TOPIC_PATTERN}")

async def _handle_charge_template_topic(msg):    
    topic = msg.topic
    payload = msg.payload

    _LOGGER.debug("PAYLOAD ROH: %s", payload.decode("utf-8")) 

    try:
        if not payload.strip().startswith(b"{"):
            _LOGGER.debug(f"Ignore incomplete charge_template Topic: {topic}")
            return

        data = json.loads(payload.decode("utf-8"))
        _LOGGER.debug("MQTT received payload:\n%s", json.dumps(data, indent=2))
        template_id = str(data.get("id"))
        template_name = data.get("name", f"Template {template_id}")

        charge_template_cache.update_charge_template(template_id, data)
        _LOGGER.debug("update_charge_template() wurde von MQTT-Handler aufgerufen")
        
        flat = flatten_json(data)
        for path, value in flat.items():
            config_key = path.replace(".", "/")
            if config_key in CHARGE_TEMPLATE_CONFIG:
                _LOGGER.debug("Queueing charge_template entity: %s %s = %s", template_id, path, value)
                queue_entity(template_id, path, value)
            else:
                _LOGGER.warning("Not configured, ignore: %s", config_key)

        _LOGGER.debug(f"Charge template received and saved: {template_id} = {template_name}")

    except Exception as e:
        _LOGGER.warning(f"Error processing charge_template topic {topic}: {e}")
