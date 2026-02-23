import os
import yaml
from pathlib import Path

from .rules import Rule

def load_config(config_path):
    """
    Загружает конфигурацию из YAML-файла.
    Возвращает словарь с обработанными путями (expanduser).
    """
    config_path = os.path.expanduser(config_path)
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    if 'watch_directory' in config:
        config['watch_directory'] = os.path.expanduser(config['watch_directory'])

    if 'rules' in config:
        for rule in config['rules']:
            if 'destination' in rule:
                rule['destination'] = os.path.expanduser(rule['destination'])

    if 'logging' in config and 'file' in config['logging']:
        config['logging']['file'] = os.path.expanduser(config['logging']['file'])

    return config

def load_rules(config):
    rules_data = config.get('rules', [])
    rules = [Rule(rule_dict) for rule_dict in rules_data]
    return rules