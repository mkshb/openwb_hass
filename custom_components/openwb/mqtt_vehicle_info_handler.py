import json
import logging
from .vehicle_cache import update_vehicle_info, update_vehicle_templates

_LOGGER = logging.getLogger(__name__)

VEHICLE_TOPIC_PATTERN = "openWB/vehicle/+/+"

def subscribe_to_vehicle_info(mqtt_client):
    mqtt_client.async_subscribe(VEHICLE_TOPIC_PATTERN, _handle_vehicle_topic, 0)

def _handle_vehicle_topic(msg):
    topic = msg.topic
    payload = msg.payload

    try:
        parts = topic.split("/")
        if len(parts) < 4:
            _LOGGER.debug(f"Ignore too short topic: {topic}")
            return

        vehicle_id_str = parts[2]
        subkey = parts[3]

        if not vehicle_id_str.isdigit():
            _LOGGER.debug(f"Ignore topic with non-numeric ID: {topic}")
            return

        vehicle_id = int(vehicle_id_str)

        if subkey == "name":
            name = json.loads(payload.decode("utf-8"))
            if name:
                update_vehicle_info(vehicle_id, name=name)
                _LOGGER.debug(f"Vehicle {vehicle_id} name updated to: {name}")

        elif subkey == "info":
            data = json.loads(payload.decode("utf-8"))
            manufacturer = data.get("manufacturer")
            model = data.get("model")
            update_vehicle_info(vehicle_id, manufacturer=manufacturer, model=model)
            _LOGGER.debug(f"Vehicle {vehicle_id} info updated: manufacturer={manufacturer}, model={model}")

        elif subkey in ("charge_template", "ev_template", "tag_id"):
            value = json.loads(payload.decode("utf-8"))
            update_vehicle_templates(vehicle_id, subkey, value)
            _LOGGER.debug(f"Vehicle {vehicle_id} {subkey} updated: {value}")

        else:
            _LOGGER.debug(f"Ignore unknown vehicle subtopic: {subkey}")

    except Exception as e:
        _LOGGER.warning(f"Error processing vehicle topic {topic} = {payload}: {e}")
