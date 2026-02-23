import os
import re
import yaml
from pathlib import Path

from .rules import Rule


def load_config(config_path):
    """
    Загружает конфигурацию из YAML-файла.
    Возвращает словарь с обработанными путями (expanduser) и скомпилированными паттернами.
    """
    config_path = os.path.expanduser(config_path)
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Обработка путей с тильдой
    if 'watch_directory' in config:
        config['watch_directory'] = os.path.expanduser(config['watch_directory'])

    if 'rules' in config:
        for rule in config['rules']:
            if 'destination' in rule:
                rule['destination'] = os.path.expanduser(rule['destination'])

    if 'logging' in config and 'file' in config['logging']:
        config['logging']['file'] = os.path.expanduser(config['logging']['file'])

    # Обработка списка разрешённых подпапок
    process_subdirs = config.get('process_subdirs', [])

    # По умолчанию обрабатываем только корень
    if not process_subdirs:
        process_subdirs = ["."]
        config['process_subdirs'] = process_subdirs

    # Разделяем специальный маркер корня и паттерны для подпапок
    root_allowed = False
    subdir_patterns = []

    for pattern in process_subdirs:
        if pattern == ".":
            root_allowed = True
            continue

        try:
            if '*' in pattern or '?' in pattern:
                # Конвертируем wildcard в regex
                regex_pattern = pattern.replace('.', '\\.').replace('*', '.*').replace('?', '.')
                subdir_patterns.append(re.compile(f"^{regex_pattern}$"))
            else:
                # Точное совпадение
                subdir_patterns.append(re.compile(f"^{re.escape(pattern)}$"))
        except re.error as e:
            print(f"Warning: Invalid pattern '{pattern}', using exact match: {e}")
            subdir_patterns.append(re.compile(f"^{re.escape(pattern)}$"))

    config['root_allowed'] = root_allowed
    config['subdir_patterns'] = subdir_patterns

    # Загружаем настройки режима демона
    daemon_mode = config.get('daemon_mode', {})
    mode_type = daemon_mode.get('type', 'watchdog')

    if mode_type == 'interval':
        interval = daemon_mode.get('interval', 300)
        # Поддерживаем разные единицы измерения
        unit = daemon_mode.get('unit', 'seconds')
        if unit == 'minutes':
            interval *= 60
        elif unit == 'hours':
            interval *= 3600
        elif unit == 'days':
            interval *= 86400

        config['daemon_interval'] = interval
        config['daemon_unit'] = unit

    elif mode_type == 'cron':
        cron_expr = daemon_mode.get('schedule')
        if not cron_expr:
            # Значение по умолчанию: каждый час
            cron_expr = "0 * * * *"
        config['daemon_cron'] = cron_expr

    config['daemon_type'] = mode_type

    # ВАЖНО: возвращаем ТОЛЬКО config, не кортеж!
    return config


def load_rules(config):
    """
    Загружает правила из конфигурации.
    Возвращает список объектов Rule.
    """
    rules_data = config.get('rules', [])
    rules = [Rule(rule_dict) for rule_dict in rules_data]
    return rules


def is_subdir_allowed(filepath, watch_dir, root_allowed, subdir_patterns):
    """
    Проверяет, находится ли файл в разрешённой подпапке.
    """
    try:
        rel_path = os.path.relpath(filepath, watch_dir)
    except ValueError:
        return False

    # Файл в корневой папке
    if os.sep not in rel_path:
        return root_allowed

    # Файл в подпапке
    first_subdir = rel_path.split(os.sep)[0]

    for pattern in subdir_patterns:
        if pattern.search(first_subdir):
            return True

    return False


def get_allowed_subdirs(watch_dir, subdir_patterns):
    """
    Возвращает список имён подпапок, которые разрешены для обработки.
    """
    allowed = []
    try:
        for item in os.listdir(watch_dir):
            item_path = os.path.join(watch_dir, item)
            if os.path.isdir(item_path):
                for pattern in subdir_patterns:
                    if pattern.search(item):
                        allowed.append(item)
                        break
    except OSError as e:
        print(f"Warning: Cannot scan directory {watch_dir}: {e}")

    return allowed