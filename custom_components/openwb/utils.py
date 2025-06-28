def flatten_json(y, sep='.'):
    out = {}

    def flatten(x, prefix=''):
        if isinstance(x, dict):
            for k, v in x.items():
                flatten(v, f"{prefix}{k}{sep}")
        elif isinstance(x, list):
            for i, v in enumerate(x):
                flatten(v, f"{prefix}{i}{sep}")
        else:
            out[prefix[:-1]] = x  # remove trailing sep

    flatten(y)
    return out


def unflatten_path(path: str, value):
    parts = path.split("/")
    result = current = {}
    for part in parts[:-1]:
        current[part] = {}
        current = current[part]
    current[parts[-1]] = value
    return result

def update_entity_name_from_cache(entity, devtype, dev_id, key, get_info_fn):

    if not hasattr(entity, "_attr_name") or not hasattr(entity, "_key"):
        return

    try:
        info = get_info_fn(int(dev_id))
        if not info:
            return

        display_name = info.get("name") or f"{devtype.upper()} {dev_id}"
        entity._attr_name = f"openWB – {display_name} – {key.replace('_', ' ').title()}"

        import logging
        logging.getLogger(__name__).info(f"Displayname: {display_name}")

    except Exception as e:
        import logging
        logging.getLogger(__name__).info(f"update_entity_name_from_cache failed: {e}")
