import json
import re
import logging
from .device_cache import update_device_name

_LOGGER = logging.getLogger(__name__)

CONFIG_TOPIC = "openWB/system/device/+/component/+/config"

def subscribe_to_device_configs(mqtt_client):
    """Subscribe to all openWB device component configs via MQTT."""
    mqtt_client.async_subscribe(CONFIG_TOPIC, _handle_component_config_message, 0)
    _LOGGER.debug(f"Subscribed to: {CONFIG_TOPIC}")

def _handle_component_config_message(msg):
    """Callback for received device configs."""
    topic = msg.topic
    payload = msg.payload

    match = re.match(r"openWB/system/device/\d+/component/(\d+)/config", topic)
    if not match:
        _LOGGER.warning(f"Ignore unknown config topic: {topic}")
        return

    component_id = int(match.group(1))

    try:
        config = json.loads(payload.decode("utf-8"))
        device_type = config.get("type")
        name = config.get("name")
        info = config.get("info", {})
        manufacturer = info.get("manufacturer")
        model = info.get("model")
        if device_type and name:
          update_device_name(device_type, component_id, name, manufacturer, model)
          _LOGGER.debug(f"Cached: {device_type}/{component_id} = '{name}'")
        else:
            _LOGGER.debug(f"Incomplete config received: {config}")
    except Exception as e:
        _LOGGER.exception(f"Error processing device {topic}: {e}")
