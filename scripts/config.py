import os
import yaml


def load_config(config_path="./config.yaml"):
    # Load YAML first as defaults
    with open(config_path, "r") as file:
        configs = yaml.safe_load(file)

    # Override with environment variables (higher priority)
    # Convert string 'true'/'false' to boolean for specific keys
    bool_keys = ['ENABLE_LOCAL', 'ENABLE_API', 'WEB_HEADLESS', 'OPTIMIZE_IMAGES', 'DOC_REFINE', 'DARK_MODE']
    int_keys = ['MAX_TOKENS', 'REQUEST_INTERVAL', 'WEB_VIEWPORT_WIDTH', 'WEB_VIEWPORT_HEIGHT',
                'IMAGE_MAX_WIDTH', 'IMAGE_MAX_HEIGHT', 'IMAGE_QUALITY', 'MAX_ROUNDS', 'MIN_DIST']

    for key in configs.keys():
        if key in os.environ:
            value = os.environ[key]
            # Type conversion
            if key in bool_keys:
                configs[key] = value.lower() in ('true', '1', 'yes')
            elif key in int_keys:
                configs[key] = int(value)
            else:
                configs[key] = value

    return configs
