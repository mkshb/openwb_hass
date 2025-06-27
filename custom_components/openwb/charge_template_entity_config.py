CHARGE_TEMPLATE_CONFIG = {
    "id": {
        "type": "text"
    },
    "name": {
        "type": "text"
    },
    "prio": {
        "type": "switch"
    },
    "load_default": {
        "type": "switch"
    },
    "time_charging/active": {
        "type": "switch"
    },

    # chargemode selected
    "chargemode/selected": {
        "type": "select",
        "options": [
            "instant_charging",
            "eco_charging",
            "pv_charging",
            "scheduled_charging",
            "stop"
        ]
    },

    # eco_charging
    "chargemode/eco_charging/current": {
        "type": "number", "min": 6, "max": 32, "step": 1, "unit": "A"
    },
    "chargemode/eco_charging/dc_current": {
        "type": "number", "min": 0, "max": 500, "step": 1, "unit": "A"
    },
    "chargemode/eco_charging/limit/selected": {
        "type": "select", "options": ["none", "amount", "soc"]
    },
    "chargemode/eco_charging/limit/amount": {
        "type": "number",
        "min": 0,
        "max": 100000,
        "step": 1000,
        "unit": "Wh" 
    },
    "chargemode/eco_charging/limit/soc": {
        "type": "number", "min": 0, "max": 100, "step": 1, "unit": "%"
    },
    "chargemode/eco_charging/max_price": {
        "type": "number", "min": 0.0001, "max": 0.001, "step": 0.001, "unit": "ct/kWh"
    },
    "chargemode/eco_charging/phases_to_use": {
        "type": "select", "options": [0, 1, 3]
    },

    # pv_charging
    "chargemode/pv_charging/dc_min_current": {
        "type": "number", "min": 0, "max": 500, "step": 1, "unit": "A"
    },
    "chargemode/pv_charging/dc_min_soc_current": {
        "type": "number", "min": 0, "max": 500, "step": 1, "unit": "A"
    },
    "chargemode/pv_charging/feed_in_limit": {
        "type": "switch"
    },
    "chargemode/pv_charging/limit/selected": {
        "type": "select", "options": ["none", "amount", "soc"]
    },
    "chargemode/pv_charging/limit/amount": {
        "type": "number", "min": 0, "max": 100000, "step": 1000, "unit": "Wh"
    },
    "chargemode/pv_charging/limit/soc": {
        "type": "number", "min": 0, "max": 100, "step": 1, "unit": "%"
    },
    "chargemode/pv_charging/min_current": {
        "type": "number", "min": 0, "max": 32, "step": 1, "unit": "A"
    },
    "chargemode/pv_charging/min_soc_current": {
        "type": "number", "min": 0, "max": 32, "step": 1, "unit": "A"
    },
    "chargemode/pv_charging/min_soc": {
        "type": "number", "min": 0, "max": 100, "step": 1, "unit": "%"
    },
    "chargemode/pv_charging/phases_to_use": {
        "type": "select", "options": [0, 1, 3]
    },
    "chargemode/pv_charging/phases_to_use_min_soc": {
        "type": "select", "options": [0, 1, 3]
    },

    # instant_charging
    "chargemode/instant_charging/current": {
        "type": "number", "min": 6, "max": 32, "step": 1, "unit": "A"
    },
    "chargemode/instant_charging/dc_current": {
        "type": "number", "min": 0, "max": 500, "step": 1, "unit": "A"
    },
    "chargemode/instant_charging/limit/selected": {
        "type": "select", "options": ["none", "amount", "soc"]
    },
    "chargemode/instant_charging/limit/amount": {
        "type": "number", "min": 0, "max": 100000, "step": 1000, "unit": "Wh"
    },
    "chargemode/instant_charging/limit/soc": {
        "type": "number", "min": 0, "max": 100, "step": 1, "unit": "%"
    },
    "chargemode/instant_charging/phases_to_use": {
        "type": "select", "options": [1, 3]
    }
}