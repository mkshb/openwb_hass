import json
import re
import logging
from .chargepoint_cache import update_chargepoint_info

_LOGGER = logging.getLogger(__name__)

CHARGEPOINT_INFO_TOPIC = "openWB/chargepoint/+/config"

def subscribe_to_chargepoint_info(mqtt_client):
    mqtt_client.async_subscribe(CHARGEPOINT_INFO_TOPIC, _handle_chargepoint_config_message, 0)
    _LOGGER.debug(f"Subscribed to: {CHARGEPOINT_INFO_TOPIC}")

def _handle_chargepoint_config_message(msg):
    topic = msg.topic
    payload = msg.payload

    match = re.match(r"openWB/chargepoint/(\d+)/config", topic)
    if not match:
        _LOGGER.debug(f"Ignore topic outside chargepoint config: {topic}")
        return

    chargepoint_id = int(match.group(1))

    try:
        config = json.loads(payload.decode("utf-8"))
        name = config.get("name")
        info = config.get("info", {}) or {}
        model = info.get("model")
        manufacturer = "openWB"

        update_chargepoint_info(chargepoint_id, name, manufacturer, model)
        _LOGGER.debug(f"Chargepoint {chargepoint_id} info updated: {name}, {manufacturer}, {model}")
    except Exception as e:
        _LOGGER.warning(f"Error processing chargepoint Config {topic}: {e}")
