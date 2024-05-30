from pathlib import Path
import yaml

def transform_values_to_strings(data: dict):
    """
    Given the dictionary 'd', it returns a new dictionary with every value
    transformed to string.
    """
    if isinstance(data, dict):
        return {k: transform_values_to_strings(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple)):
        return [transform_values_to_strings(item) for item in data]
    else:
        return str(data)


def yaml_dump(data: dict, path: Path | str):
    """Save data to a YAML after changing all paths to string."""
    data = transform_values_to_strings(data)
    
    if not isinstance(path, Path):
        path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False)