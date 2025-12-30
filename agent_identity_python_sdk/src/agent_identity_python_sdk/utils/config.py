import json
import logging
from pathlib import Path

local_config_file = '.config.json'

logger = logging.getLogger("agentidentity.utils.config")
logger.setLevel("INFO")
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())

def write_local_config(key: str, value: str, file_path: str = local_config_file):
    """
    Write a key-value pair to the local configuration file.
    
    Args:
        key (str): The configuration key to write
        value (str): The configuration value to write
        file_path (str, optional): The path to the configuration file. 
                                  Defaults to local_config_file ('.config.json').
    
    This function reads the existing configuration file (if it exists),
    updates or adds the specified key-value pair, and writes the updated
    configuration back to the file. If the file doesn't exist or is empty,
    it creates a new configuration dictionary.
    """
    if Path(file_path).exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                content = f.read().strip()
                if content:  # 检查文件是否为空
                    config_data = json.loads(content)
                else:
                    config_data = {}
            except json.JSONDecodeError:
                config_data = {}
    else:
        config_data = {}

    config_data[key] = value

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Wrote {key}: {value} to {file_path}")


def read_local_config(key: str, file_path: str = local_config_file):
    """
    Read a value from the local configuration file.

    Args:
        key (str): The configuration key to read
        file_path (str, optional): The path to the configuration file.
                                  Defaults to local_config_file ('.config.json').

    This function reads the configuration file and returns the value associated
    with the specified key. If the file doesn't exist or the key doesn't exist,
    it returns None.
    """
    if not Path(file_path).exists():
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            config_data = json.load(f)
        except json.JSONDecodeError:
            return None

    return config_data.get(key, None)
