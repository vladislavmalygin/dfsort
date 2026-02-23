"""
Конфигуратор для dfsort.
Создаёт, проверяет и управляет конфигурационными файлами.
Поддерживает бэкапы и интерактивное создание конфига.
"""

import os
import shutil
import sys
import re
import yaml
import questionary
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# Цвета для вывода
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    YELLOW = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Configurator:
    """
    Конфигуратор для dfsort.
    Управляет созданием, редактированием и бэкапом конфигураций.
    """

    CONFIG_DIR = Path.home() / '.config' / 'dfsort'
    CONFIG_PATH = CONFIG_DIR / 'config.yaml'
    BACKUP_DIR = CONFIG_DIR / 'backups'

    def __init__(self):
        """Инициализация конфигуратора."""
        self.config = None
        self._ensure_dirs()
        # Получаем имя текущего пользователя для универсальных путей
        self.username = os.getenv('USER') or os.getenv('USERNAME') or 'user'

    def _ensure_dirs(self):
        """Создаёт необходимые директории."""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    def _backup_current(self) -> Optional[Path]:
        """
        Создаёт бэкап текущего конфига.
        Хранит 2 последние версии.
        """
        if not self.CONFIG_PATH.exists():
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.BACKUP_DIR / f"config_{timestamp}.yaml"

        shutil.copy2(self.CONFIG_PATH, backup_path)

        # Удаляем старые бэкапы, оставляя только 2 последних
        backups = sorted(self.BACKUP_DIR.glob("config_*.yaml"))
        for old_backup in backups[:-2]:
            old_backup.unlink()

        return backup_path

    def _restore_from_backup(self) -> bool:
        """Восстанавливает конфиг из последнего бэкапа."""
        backups = sorted(self.BACKUP_DIR.glob("config_*.yaml"))
        if not backups:
            return False

        latest = backups[-1]
        shutil.copy2(latest, self.CONFIG_PATH)
        return True

    def _get_universal_path(self, path: str) -> str:
        """
        Преобразует абсолютный путь в универсальный с ~.
        Например: /home/username/Загрузки -> ~/Загрузки
        """
        home = str(Path.home())
        if path.startswith(home):
            return path.replace(home, "~")
        return path

    def load_or_create(self) -> Dict:
        """
        Загружает существующий конфиг или создаёт новый.
        При первом запуске спрашивает пользователя.
        """
        if self.CONFIG_PATH.exists():
            print(f"{Colors.GREEN}✓ Найден существующий конфиг: {self.CONFIG_PATH}{Colors.END}")
            choice = questionary.select(
                "Что делаем?",
                choices=[
                    {"name": "📝 Редактировать существующий конфиг", "value": "edit"},
                    {"name": "🔄 Создать новый конфиг (старый будет сохранён в бэкап)", "value": "new"},
                    {"name": "📋 Просмотреть текущий конфиг", "value": "view"},
                    {"name": "📂 Открыть папку с конфигами", "value": "open"},
                    {"name": "🚀 Запустить программу с текущим конфигом", "value": "run"}
                ]
            ).ask()

            if choice == "edit":
                self._edit_config()
                return self.load_config()
            elif choice == "new":
                self._backup_current()
                return self._create_interactive()
            elif choice == "view":
                self._view_config()
                return self.load_or_create()
            elif choice == "open":
                self._open_config_dir()
                return self.load_or_create()
            else:  # "run"
                return self.load_config()
        else:
            print(f"{Colors.CYAN}🆕 Первый запуск. Создаём конфигурацию...{Colors.END}")
            return self._create_interactive()

    def load_config(self) -> Dict:
        """Загружает конфиг из файла."""
        with open(self.CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def save_config(self, config: Dict):
        """Сохраняет конфиг в файл."""
        with open(self.CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        print(f"{Colors.GREEN}✓ Конфиг сохранён: {self.CONFIG_PATH}{Colors.END}")

    def _create_interactive(self) -> Dict:
        """
        Интерактивное создание конфига.
        Спрашивает пользователя пошагово.
        """
        print(f"\n{Colors.BOLD}{Colors.HEADER}=== СОЗДАНИЕ КОНФИГУРАЦИИ DFSORT ==={Colors.END}")
        print(f"{Colors.CYAN}Я помогу настроить автосортировщик файлов.{Colors.END}\n")

        config = {}

        # 1. Режим создания
        mode = questionary.select(
            "Как создать конфиг?",
            choices=[
                {"name": "🪄 Интерактивный режим (программа спросит всё необходимое)", "value": "interactive"},
                {"name": "✏️ Я создам конфиг вручную (откроется редактор)", "value": "manual"},
                {"name": "📋 Скопировать пример и отредактировать", "value": "example"}
            ]
        ).ask()

        if mode == "manual":
            self._create_empty_config()
            self._edit_config()
            return self.load_config()

        elif mode == "example":
            self._create_example_config()
            self._edit_config()
            return self.load_config()

        # Интерактивный режим
        print(f"\n{Colors.BOLD}📁 Основные настройки:{Colors.END}")

        # Watch directory - показываем универсальный путь
        default_watch = self._get_universal_path(str(Path.home() / 'Загрузки'))
        watch_dir = questionary.path(
            "За какой папкой следить?",
            default=default_watch
        ).ask()
        config['watch_directory'] = watch_dir

        # Time to move
        ttm = questionary.text(
            "Через сколько часов обрабатывать файлы? (0 = сразу)",
            default="48"
        ).ask()
        config['time_to_move'] = int(ttm) if ttm else 0

        # Режим демона
        print(f"\n{Colors.BOLD}🤖 Режим работы демона:{Colors.END}")
        daemon_type = questionary.select(
            "Как часто проверять файлы?",
            choices=[
                {"name": "⚡ Мгновенно (watchdog) - реагировать сразу", "value": "watchdog"},
                {"name": "⏱️ Через интервал - проверять каждые N секунд/минут/часов", "value": "interval"},
                {"name": "📅 По расписанию (cron) - задать сложное расписание", "value": "cron"}
            ]
        ).ask()

        daemon_mode = {"type": daemon_type}

        if daemon_type == "interval":
            interval_value = questionary.text(
                "Каждые сколько?",
                default="5"
            ).ask()
            interval_unit = questionary.select(
                "Единица измерения:",
                choices=[
                    {"name": "секунды", "value": "seconds"},
                    {"name": "минуты", "value": "minutes"},
                    {"name": "часы", "value": "hours"},
                    {"name": "дни", "value": "days"}
                ]
            ).ask()
            daemon_mode["interval"] = int(interval_value)
            daemon_mode["unit"] = interval_unit

        elif daemon_type == "cron":
            print(f"\n{Colors.CYAN}Формат cron: минута час день месяц день_недели{Colors.END}")
            print(f"{Colors.CYAN}Примеры:{Colors.END}")
            print("  0 9 * * *     - каждый день в 9:00")
            print("  30 18 * * 1   - каждый понедельник в 18:30")
            print("  0 */2 * * *   - каждые 2 часа")
            cron_expr = questionary.text(
                "Введите cron-выражение:",
                default="0 9 * * *"
            ).ask()
            daemon_mode["schedule"] = cron_expr

        config['daemon_mode'] = daemon_mode

        # Подпапки для обработки
        print(f"\n{Colors.BOLD}📂 Какие подпапки обрабатывать?{Colors.END}")
        print(f"{Colors.CYAN}По умолчанию обрабатывается только корень (.){Colors.END}")

        subdirs = []
        if questionary.confirm("Добавить корневую папку (.)?", default=True).ask():
            subdirs.append(".")

        # Предлагаем пользователю ввести свои папки (не предлагаем стандартные)
        if questionary.confirm("Хотите добавить подпапки для обработки?", default=False).ask():
            while True:
                pattern = questionary.text(
                    "Введите имя подпапки или паттерн (например: temp*, *.part)\n"
                    "Или оставьте пустым для завершения:"
                ).ask()
                if not pattern:
                    break
                subdirs.append(pattern)

        config['process_subdirs'] = subdirs if subdirs else ["."]

        # Правила сортировки
        print(f"\n{Colors.BOLD}📋 Правила сортировки:{Colors.END}")
        rules = []

        # Список доступных типов файлов (без предустановленных действий)
        file_types = [
            {"name": "📷 Изображения (jpg, png, gif, ...)", "value": "images"},
            {"name": "🎬 Видео (mp4, avi, mkv, ...)", "value": "videos"},
            {"name": "🎵 Музыка (mp3, flac, wav, ...)", "value": "music"},
            {"name": "📄 Документы (pdf, doc, xls, ...)", "value": "documents"},
            {"name": "🗜️ Архивы (zip, rar, 7z, ...)", "value": "archives"},
            {"name": "💿 Образы дисков (iso, img, ...)", "value": "disk_images"},
            {"name": "🧲 Торренты (.torrent)", "value": "torrents"},
            {"name": "⚙️ Другой тип (настрою сам)", "value": "custom"}
        ]

        while True:
            selected = questionary.select(
                "Выберите тип файлов для добавления правила:",
                choices=file_types + [{"name": "✅ Закончить добавление правил", "value": "done"}]
            ).ask()

            if selected == "done":
                break

            if selected == "custom":
                rule = self._create_custom_rule_interactive()
                if rule:
                    rules.append(rule)
            else:
                rule = self._create_rule_for_type(selected)
                if rule:
                    rules.append(rule)

        config['rules'] = rules

        # Логирование
        print(f"\n{Colors.BOLD}📝 Настройки логирования:{Colors.END}")
        default_log = self._get_universal_path(str(Path.home() / '.local' / 'share' / 'dfsort' / 'dfsort.log'))
        config['logging'] = {
            'file': questionary.path("Путь к лог-файлу:", default=default_log).ask(),
            'level': questionary.select(
                "Уровень логирования:",
                choices=[
                    {"name": "DEBUG - подробные логи", "value": "DEBUG"},
                    {"name": "INFO - основные события", "value": "INFO"},
                    {"name": "WARNING - только предупреждения", "value": "WARNING"},
                    {"name": "ERROR - только ошибки", "value": "ERROR"}
                ]
            ).ask()
        }

        # Сохраняем конфиг
        self.save_config(config)

        print(f"\n{Colors.GREEN}✓ Конфиг успешно создан!{Colors.END}")
        return config

    def _create_rule_for_type(self, file_type: str) -> Optional[Dict]:
        """
        Создаёт правило для выбранного типа файлов.
        Спрашивает действие и назначение.
        """
        print(f"\n{Colors.CYAN}--- Настройка правила для {file_type} ---{Colors.END}")

        # Базовые паттерны для каждого типа
        type_patterns = {
            "images": {
                "name": "Images",
                "patterns": [".*\\.(jpg|jpeg|png|gif|bmp|svg|webp|ico)$"],
                "mime_types": ["image/.*"]
            },
            "videos": {
                "name": "Videos",
                "patterns": [".*\\.(mp4|avi|mkv|mov|wmv|flv|webm|m4v|mpg|mpeg)$"],
                "mime_types": ["video/.*"]
            },
            "music": {
                "name": "Music",
                "patterns": [".*\\.(mp3|flac|wav|aac|ogg|m4a|wma|opus)$"],
                "mime_types": ["audio/.*"]
            },
            "documents": {
                "name": "Documents",
                "patterns": [".*\\.(pdf|docx?|xlsx?|pptx?|txt|odt|ods|odp|rtf|md)$"],
                "mime_types": ["application/pdf", "application/msword", "text/.*"]
            },
            "archives": {
                "name": "Archives",
                "patterns": [".*\\.(zip|tar\\.gz|tgz|rar|7z|gz|xz|bz2)$"],
                "mime_types": ["application/zip", "application/x-tar", "application/x-gzip"]
            },
            "disk_images": {
                "name": "Disk Images",
                "patterns": [".*\\.(iso|img|bin|cue|nrg|mdf|dmg)$"],
                "mime_types": ["application/x-iso9660-image", "application/octet-stream"]
            },
            "torrents": {
                "name": "Torrent files",
                "patterns": [".*\\.torrent$"],
                "mime_types": ["application/x-bittorrent"]
            }
        }

        if file_type not in type_patterns:
            return None

        base = type_patterns[file_type]
        rule = {
            "name": base["name"],
            "patterns": base["patterns"],
            "mime_types": base["mime_types"]
        }

        # Спрашиваем действие
        action = questionary.select(
            f"Что делать с {base['name']}?",
            choices=[
                {"name": "📂 Переместить в папку", "value": "move"},
                {"name": "🗑️ Удалить", "value": "delete"},
                {"name": "❌ Пропустить (не добавлять правило)", "value": "skip"}
            ]
        ).ask()

        if action == "skip":
            return None
        elif action == "delete":
            rule["action"] = "delete"
            return rule
        else:  # move
            rule["action"] = "move"

            # Спрашиваем куда перемещать
            default_dest = self._get_universal_path(str(Path.home() / self._get_default_dest(file_type)))
            dest = questionary.path(
                f"Куда перемещать {base['name']}?",
                default=default_dest
            ).ask()
            rule["destination"] = dest

            # Спрашиваем про конфликты
            rule["conflict"] = questionary.select(
                "Как поступать при совпадении имён?",
                choices=[
                    {"name": "📝 Переименовать (файл_1.ext)", "value": "rename"},
                    {"name": "✍️ Перезаписать", "value": "overwrite"},
                    {"name": "⏭️ Пропустить", "value": "skip"}
                ]
            ).ask()

            # Спрашиваем про подпапки по дате
            if questionary.confirm("Создавать подпапки по дате?", default=False).ask():
                date_format = questionary.select(
                    "Формат даты:",
                    choices=[
                        {"name": "📅 Год/Месяц (2026/02)", "value": "%Y/%m"},
                        {"name": "📅 Год/Месяц/День (2026/02/23)", "value": "%Y/%m/%d"},
                        {"name": "📅 Год-Месяц (2026-02)", "value": "%Y-%m"},
                        {"name": "📅 Свой формат", "value": "custom"}
                    ]
                ).ask()

                if date_format == "custom":
                    date_format = questionary.text(
                        "Введите формат даты (например: %Y_%m):"
                    ).ask()

                rule["subfolder_by_date"] = date_format

            return rule

    def _get_default_dest(self, file_type: str) -> str:
        """Возвращает папку назначения по умолчанию для типа файлов."""
        defaults = {
            "images": "Изображения",
            "videos": "Видео",
            "music": "Музыка",
            "documents": "Документы",
            "archives": "Загрузки/Архивы",
            "disk_images": "Загрузки/Образы",
            "torrents": "Загрузки"
        }
        return defaults.get(file_type, "Загрузки")

    def _create_custom_rule_interactive(self) -> Optional[Dict]:
        """Интерактивное создание пользовательского правила."""
        print(f"\n{Colors.CYAN}--- Создание пользовательского правила ---{Colors.END}")

        rule = {}

        # Имя правила
        rule['name'] = questionary.text("Название правила:").ask()
        if not rule['name']:
            return None

        # Паттерны имён
        print(f"\n{Colors.CYAN}Регулярные выражения для имён файлов:{Colors.END}")
        print(f"Пример: .*\\.(jpg|png)$")
        patterns = []
        while True:
            pattern = questionary.text("Введите regex (или оставьте пустым для завершения):").ask()
            if not pattern:
                break
            patterns.append(pattern)
        if patterns:
            rule['patterns'] = patterns

        # MIME-типы
        if questionary.confirm("Добавить MIME-типы?", default=False).ask():
            mimes = []
            while True:
                mime = questionary.text("Введите MIME-тип (например, image/*):").ask()
                if not mime:
                    break
                mimes.append(mime)
            if mimes:
                rule['mime_types'] = mimes

        # Действие
        action = questionary.select(
            "Что делать с файлами?",
            choices=[
                {"name": "📂 Переместить", "value": "move"},
                {"name": "🗑️ Удалить", "value": "delete"}
            ]
        ).ask()

        rule['action'] = action

        if action == 'move':
            dest = questionary.path("Куда перемещать?").ask()
            rule['destination'] = dest

            rule['conflict'] = questionary.select(
                "Как поступать при совпадении имён?",
                choices=[
                    {"name": "📝 Переименовать", "value": "rename"},
                    {"name": "✍️ Перезаписать", "value": "overwrite"},
                    {"name": "⏭️ Пропустить", "value": "skip"}
                ]
            ).ask()

        return rule

    def _edit_config(self):
        """Открывает конфиг в редакторе."""
        editor = os.environ.get('EDITOR', 'nano')
        os.system(f"{editor} {self.CONFIG_PATH}")

    def _view_config(self):
        """Показывает текущий конфиг."""
        if not self.CONFIG_PATH.exists():
            print(f"{Colors.FAIL}Конфиг не найден{Colors.END}")
            return

        with open(self.CONFIG_PATH, 'r', encoding='utf-8') as f:
            print(f"\n{Colors.BOLD}📄 Текущий конфиг:{Colors.END}")
            print(f.read())

    def _open_config_dir(self):
        """Открывает папку с конфигами."""
        if sys.platform == 'linux':
            os.system(f"xdg-open {self.CONFIG_DIR}")
        elif sys.platform == 'darwin':
            os.system(f"open {self.CONFIG_DIR}")
        elif sys.platform == 'win32':
            os.system(f"explorer {self.CONFIG_DIR}")

    def _create_empty_config(self):
        """Создаёт пустой конфиг."""
        empty_config = {
            'watch_directory': self._get_universal_path(str(Path.home() / 'Загрузки')),
            'time_to_move': 48,
            'process_subdirs': ['.'],
            'rules': [],
            'logging': {
                'file': self._get_universal_path(str(Path.home() / '.local' / 'share' / 'dfsort' / 'dfsort.log')),
                'level': 'INFO'
            }
        }
        self.save_config(empty_config)

    def _create_example_config(self):
        """Создаёт пример конфига с комментариями."""
        example = """# dfsort configuration file
# Автосортировщик файлов

# Папка для наблюдения
watch_directory: "~/Загрузки"

# Через сколько часов обрабатывать файлы (0 = сразу)
time_to_move: 48

# Режим работы демона
daemon_mode:
  type: "watchdog"  # watchdog, interval, cron

# Какие подпапки обрабатывать (остальные игнорируются)
process_subdirs:
  - "."          # корневая папка

# Правила сортировки (пример)
rules:
  - name: "Images"
    patterns:
      - ".*\\.(jpg|jpeg|png|gif)$"
    destination: "~/Изображения"
    action: move
    conflict: rename

# Логирование
logging:
  file: "~/.local/share/dfsort/dfsort.log"
  level: INFO
"""
        with open(self.CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.write(example)
        print(f"{Colors.GREEN}✓ Пример конфига создан{Colors.END}")


def main():
    """Точка входа для конфигуратора."""
    configurator = Configurator()

    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════╗")
    print("║        DFSORT - Конфигуратор           ║")
    print("║     Автосортировщик файлов             ║")
    print("╚════════════════════════════════════════╝")
    print(f"{Colors.END}")

    config = configurator.load_or_create()

    action = questionary.select(
        "Что делаем дальше?",
        choices=[
            {"name": "🚀 Запустить сортировщик сейчас (однократно)", "value": "once"},
            {"name": "🔄 Запустить как демон (в фоне)", "value": "daemon"},
            {"name": "⚙️  Настроить автозапуск демона", "value": "enable"},
            {"name": "📝 Продолжить редактирование", "value": "edit"},
            {"name": "❌ Выйти", "value": "exit"}
        ]
    ).ask()

    if action == "once":
        print(f"{Colors.CYAN}Запуск однократной сортировки...{Colors.END}")
        from .cli import main as dfsort_main
        sys.argv = ['dfsort', '--config', str(configurator.CONFIG_PATH), '-o']
        dfsort_main()

    elif action == "daemon":
        print(f"{Colors.CYAN}Запуск демона...{Colors.END}")
        os.system("systemctl --user start dfsort")
        os.system("systemctl --user status dfsort")
        print(f"{Colors.GREEN}✓ Демон запущен{Colors.END}")

    elif action == "enable":
        print(f"{Colors.CYAN}Настройка автозапуска демона...{Colors.END}")
        os.system("systemctl --user enable dfsort")
        os.system("systemctl --user start dfsort")
        print(f"{Colors.GREEN}✓ Демон добавлен в автозагрузку и запущен{Colors.END}")

    elif action == "edit":
        configurator._edit_config()

    else:
        print(f"{Colors.GREEN}До свидания!{Colors.END}")

    # После завершения показываем статус демона
    if action in ["daemon", "enable"]:
        print(f"\n{Colors.CYAN}Статус демона:{Colors.END}")
        os.system("systemctl --user status dfsort --no-pager")


if __name__ == '__main__':
    main()