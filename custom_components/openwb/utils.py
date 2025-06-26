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

