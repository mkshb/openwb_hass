SENSOR_DEFINITION_MAP = {
    "currents": {
        "unit": "A",
        "icon": "mdi:current-ac",
        "device_class": "current",
        "state_class": "measurement",
    },
    "max_currents": {
        "unit": "A",
        "icon": "mdi:current-ac",
        "device_class": "current",
        "state_class": "measurement",
    },
    "powers": {
        "unit": "W",
        "icon": "mdi:flash",
        "device_class": "power",
        "state_class": "measurement",
    },
    "power": {
        "unit": "W",
        "icon": "mdi:flash",
        "device_class": "power",
        "state_class": "measurement",
    },
    "voltages": {
        "unit": "V",
        "icon": "mdi:flash",
        "device_class": "voltage",
        "state_class": "measurement",
    },
    "imported": {
        "unit": "Wh",
        "icon": "mdi:transmission-tower",
        "device_class": "energy",
        "state_class": "total_increasing",
    },
    "exported": {
        "unit": "Wh",
        "icon": "mdi:transmission-tower",
        "device_class": "energy",
        "state_class": "total_increasing",
    },
    "frequency": {
        "unit": "Hz",
        "icon": "mdi:sine-wave",
        "device_class": "frequency",
        "state_class": "measurement",
    },
    # Optional: Default-Werte
    "fault": {
        "icon": "mdi:alert-circle-outline",
    },
    "default": {
        "icon": "mdi:ev-station",
    },
}
