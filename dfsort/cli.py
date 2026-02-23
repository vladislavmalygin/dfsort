import argparse
import logging
import time
import sys
import os
import signal
import shutil
import questionary
from pathlib import Path
from watchdog.observers import Observer

from .config import load_config
from .config import load_rules
from .logger import setup_logger
from .handlers import SorterEventHandler
from .core import process_all_files
from .scheduler import FileScheduler
from .configurator import Configurator, Colors

# Глобальные переменные для graceful shutdown
scheduler = None
observer = None

# Версия программы
VERSION = "1.0.2"

def check_and_create_config(config_path):
    """
    Проверяет существование конфига и запускает конфигуратор при необходимости.
    Возвращает загруженный конфиг.
    """
    expanded_path = os.path.expanduser(config_path)

    # Если пользовательский конфиг не найден, пробуем системный
    if not os.path.exists(expanded_path):
        system_config = "/etc/dfsort/config.yaml"
        if os.path.exists(system_config):
            print(f"{Colors.CYAN}Используется системный конфиг: {system_config}{Colors.END}")
            return load_config(system_config)

def print_logo():
    """Выводит логотип программы."""
    logo = f"""
{Colors.BOLD}{Colors.HEADER}╔══════════════════════════════════════════════════════════╗
║                                                              ║
║   ██████╗ ███████╗███████╗ ██████╗ ██████╗ ████████╗       ║
║   ██╔══██╗██╔════╝██╔════╝██╔═══██╗██╔══██╗╚══██╔══╝       ║
║   ██║  ██║█████╗  ███████╗██║   ██║██████╔╝   ██║          ║
║   ██║  ██║██╔══╝  ╚════██║██║   ██║██╔══██╗   ██║          ║
║   ██████╔╝██║     ███████║╚██████╔╝██║  ██║   ██║          ║
║   ╚═════╝ ╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝          ║
║                                                              ║
║              File Sorter - Автосортировщик файлов           ║
║                         Версия {VERSION}                        ║
╚══════════════════════════════════════════════════════════════╝{Colors.END}
"""
    print(logo)


def print_help():
    """Выводит подробную справку по командам."""
    help_text = f"""
{Colors.BOLD}{Colors.CYAN}ДОСТУПНЫЕ КОМАНДЫ:{Colors.END}

{Colors.BOLD}ОСНОВНЫЕ:{Colors.END}
  {Colors.GREEN}dfsort{Colors.END}                    Запуск в режиме watchdog (мгновенное отслеживание)
  {Colors.GREEN}dfsort -o{Colors.END}                Однократная обработка всех файлов в папке
  {Colors.GREEN}dfsort -d{Colors.END}                Запуск в режиме демона (для systemd)

{Colors.BOLD}УПРАВЛЕНИЕ КОНФИГУРАЦИЕЙ:{Colors.END}
  {Colors.GREEN}dfsort --configure{Colors.END}        Запуск мастера настройки конфигурации
  {Colors.GREEN}dfsort --manage-config{Colors.END}    Управление конфигом (просмотр/удаление/бэкап/восстановление)
  {Colors.GREEN}dfsort -c ФАЙЛ{Colors.END}             Использовать указанный конфиг-файл

{Colors.BOLD}ДОПОЛНИТЕЛЬНО:{Colors.END}
  {Colors.GREEN}dfsort -h{Colors.END}                 Показать эту справку
  {Colors.GREEN}dfsort --version{Colors.END}          Показать версию программы

{Colors.BOLD}ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ:{Colors.END}
  {Colors.CYAN}# Первый запуск - создание конфига{Colors.END}
  dfsort

  {Colors.CYAN}# Запуск конфигуратора{Colors.END}
  dfsort --configure

  {Colors.CYAN}# Обработать все существующие файлы{Colors.END}
  dfsort -o

  {Colors.CYAN}# Удалить текущий конфиг и создать новый{Colors.END}
  dfsort --manage-config

  {Colors.CYAN}# Запуск с другим конфигом{Colors.END}
  dfsort -c ~/my-config.yaml

{Colors.BOLD}РЕЖИМЫ РАБОТЫ:{Colors.END}
  {Colors.YELLOW}watchdog{Colors.END}   - мгновенная реакция на новые файлы (по умолчанию)
  {Colors.YELLOW}interval{Colors.END}   - проверка через заданные интервалы
  {Colors.YELLOW}cron{Colors.END}       - проверка по расписанию (cron-формат)

{Colors.BOLD}ФАЙЛЫ КОНФИГУРАЦИИ:{Colors.END}
  Конфиг:           ~/.config/dfsort/config.yaml
  Бэкапы:           ~/.config/dfsort/backups/
  Логи:             ~/.local/share/dfsort/dfsort.log

{Colors.CYAN}Подробная документация: https://github.com/vladislavmalygin/dfsort{Colors.END}
"""
    print(help_text)


def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown."""
    logger = logging.getLogger('dfsort')
    logger.info(f"Получен сигнал {signum}, завершаем работу...")

    global scheduler, observer

    if scheduler:
        scheduler.stop()

    if observer:
        observer.stop()
        observer.join()

    sys.exit(0)


def manage_config(config_path):
    """
    Управление конфигурационными файлами:
    - удалить текущий конфиг
    - заархивировать текущий конфиг
    - восстановить из бэкапа
    """
    expanded_path = os.path.expanduser(config_path)
    config_dir = os.path.dirname(expanded_path)
    backup_dir = os.path.join(config_dir, 'backups')

    print(f"\n{Colors.BOLD}{Colors.HEADER}=== УПРАВЛЕНИЕ КОНФИГУРАЦИЕЙ ==={Colors.END}")

    if not os.path.exists(expanded_path):
        print(f"{Colors.WARNING}Конфиг не найден: {expanded_path}{Colors.END}")
        return

    # Показываем текущий конфиг
    print(f"\n{Colors.CYAN}Текущий конфиг:{Colors.END} {expanded_path}")
    print(f"{Colors.CYAN}Содержимое:{Colors.END}")
    with open(expanded_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # Выводим с отступами для читаемости
        for line in content.split('\n'):
            print(f"  {line}")

    choices = [
        {"name": "🗑️ Удалить текущий конфиг", "value": "delete"},
        {"name": "📦 Создать бэкап и удалить", "value": "backup_delete"},
    ]

    # Добавляем возможность восстановления, если есть бэкапы
    if os.path.exists(backup_dir):
        backups = sorted(Path(backup_dir).glob("config_*.yaml"))
        if backups:
            choices.append({"name": "🔄 Восстановить из бэкапа", "value": "restore"})

    choices.append({"name": "❌ Отмена", "value": "cancel"})

    action = questionary.select(
        "Что делаем с конфигом?",
        choices=choices
    ).ask()

    if action == "delete":
        if questionary.confirm("Вы уверены? Это действие нельзя отменить!", default=False).ask():
            os.remove(expanded_path)
            print(f"{Colors.GREEN}✓ Конфиг удалён{Colors.END}")

    elif action == "backup_delete":
        # Создаём бэкап
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, f"config_{timestamp}.yaml")
        shutil.copy2(expanded_path, backup_path)
        print(f"{Colors.GREEN}✓ Бэкап создан: {backup_path}{Colors.END}")

        # Удаляем
        os.remove(expanded_path)
        print(f"{Colors.GREEN}✓ Конфиг удалён{Colors.END}")

    elif action == "restore":
        backups = sorted(Path(backup_dir).glob("config_*.yaml"))
        backup_choices = []
        for b in backups:
            # Показываем дату из имени файла
            date_str = b.stem.replace('config_', '').replace('_', ' ')
            backup_choices.append({"name": f"📅 {date_str}", "value": str(b)})

        selected = questionary.select(
            "Выберите бэкап для восстановления:",
            choices=backup_choices + [{"name": "❌ Отмена", "value": "cancel"}]
        ).ask()

        if selected and selected != "cancel":
            # Создаём бэкап текущего конфига
            if os.path.exists(expanded_path):
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                current_backup = os.path.join(backup_dir, f"config_before_restore_{timestamp}.yaml")
                shutil.copy2(expanded_path, current_backup)
                print(f"{Colors.GREEN}✓ Текущий конфиг сохранён в бэкап{Colors.END}")

            # Восстанавливаем выбранный бэкап
            shutil.copy2(selected, expanded_path)
            print(f"{Colors.GREEN}✓ Конфиг восстановлен из бэкапа{Colors.END}")

    else:  # cancel
        print(f"{Colors.CYAN}Операция отменена{Colors.END}")


def check_and_create_config(config_path):
    """
    Проверяет существование конфига и запускает конфигуратор при необходимости.
    Возвращает загруженный конфиг.
    """
    expanded_path = os.path.expanduser(config_path)

    if not os.path.exists(expanded_path):
        print(f"{Colors.WARNING}⚙️ Конфигурационный файл не найден.{Colors.END}")
        print(f"{Colors.CYAN}Запускаем мастер настройки...{Colors.END}\n")

        configurator = Configurator()
        configurator.load_or_create()

        # Загружаем конфиг через load_config для обработки путей и паттернов
        return load_config(config_path)
    else:
        # Конфиг существует, загружаем
        try:
            return load_config(config_path)
        except Exception as e:
            print(f"{Colors.FAIL}❌ Ошибка загрузки конфига: {e}{Colors.END}")
            print(f"{Colors.CYAN}Запускаем конфигуратор для исправления...{Colors.END}")

            configurator = Configurator()
            configurator.load_or_create()
            return load_config(config_path)


def main():
    global scheduler, observer

    # Создаём парсер с подробным описанием
    parser = argparse.ArgumentParser(
        description="File auto-sorter - автоматическая сортировка файлов",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # Отключаем стандартный help, чтобы использовать свой
        epilog="""
Дополнительную информацию можно получить на странице проекта:
https://github.com/yourname/dfsort
        """
    )

    # Основные аргументы
    parser.add_argument('--config', '-c', default='~/.config/dfsort/config.yaml',
                        help='Path to configuration file (default: ~/.config/dfsort/config.yaml)')
    parser.add_argument('-o', '--once', action='store_true', dest='once',
                        help='Process all existing files and exit')
    parser.add_argument('-d', '--daemon', action='store_true', dest='daemon',
                        help='Run in foreground (for systemd)')

    # Управление конфигурацией
    parser.add_argument('--configure', action='store_true',
                        help='Run configuration wizard')
    parser.add_argument('--manage-config', action='store_true',
                        help='Manage configuration (delete/backup/restore)')

    # Информационные аргументы
    parser.add_argument('-h', '--help', action='store_true',
                        help='Show this help message and exit')
    parser.add_argument('--version', '-v', action='store_true',
                        help='Show version and exit')

    args = parser.parse_args()

    # Показываем логотип при любом запуске, кроме --version
    if not args.version:
        print_logo()

    # Если запрошен help
    if args.help:
        print_help()
        return

    # Если запрошена версия
    if args.version:
        print(f"dfsort version {VERSION}")
        return

    # Если запрошено управление конфигом
    if args.manage_config:
        manage_config(args.config)
        return

    # Если запрошен конфигуратор
    if args.configure:
        configurator = Configurator()
        configurator.load_or_create()
        return

    # Если нет аргументов, показываем краткую подсказку
    if len(sys.argv) == 1:
        print(
            f"{Colors.CYAN}Запуск без аргументов. Используйте {Colors.GREEN}dfsort -h{Colors.CYAN} для справки.{Colors.END}")
        print(f"{Colors.CYAN}Начинаем мониторинг с конфигом по умолчанию...{Colors.END}\n")

    # Проверяем и создаём конфиг при необходимости
    try:
        config = check_and_create_config(args.config)
    except Exception as e:
        print(f"{Colors.FAIL}❌ Критическая ошибка: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Настраиваем логирование
    log_file = config.get('logging', {}).get('file')
    log_level = config.get('logging', {}).get('level', 'INFO')
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger = setup_logger(log_file, numeric_level)

    # Проверяем директорию
    watch_dir = config.get('watch_directory')
    if not watch_dir:
        logger.error("watch_directory not specified in config")
        sys.exit(1)

    if not os.path.isdir(watch_dir):
        logger.error(f"Watch directory does not exist: {watch_dir}")

        # Предлагаем создать директорию
        response = input(f"{Colors.WARNING}Создать директорию {watch_dir}? (y/n): {Colors.END}")
        if response.lower() == 'y':
            os.makedirs(watch_dir, exist_ok=True)
            logger.info(f"Created directory: {watch_dir}")
        else:
            sys.exit(1)

    # Загружаем правила
    rules = load_rules(config)
    logger.info(f"Loaded {len(rules)} rules")

    # Получаем параметры
    min_age_hours = config.get('time_to_move', 0)
    root_allowed = config.get('root_allowed', False)
    subdir_patterns = config.get('subdir_patterns', [])
    daemon_type = config.get('daemon_type', 'watchdog')

    if min_age_hours:
        logger.info(f"Files will be processed only after {min_age_hours} hours")
    else:
        logger.info("Age check disabled (time_to_move=0)")

    logger.info(f"Root directory allowed: {root_allowed}")
    logger.info(f"Subdirectory patterns: {[p.pattern for p in subdir_patterns]}")
    logger.info(f"Daemon mode type: {daemon_type}")

    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Режим --once
    if args.once:
        logger.info(f"{Colors.CYAN}Once mode: processing all files in {watch_dir}{Colors.END}")
        start_time = time.time()

        processed, skipped, excluded, errors = process_all_files(
            directory=watch_dir,
            rules=rules,
            logger=logger,
            root_allowed=root_allowed,
            subdir_patterns=subdir_patterns,
            min_age_hours=min_age_hours
        )

        elapsed_time = time.time() - start_time
        logger.info(f"{Colors.GREEN}✅ Once mode completed in {elapsed_time:.2f} seconds{Colors.END}")
        logger.info(f"📊 Statistics: {processed} processed, {skipped} skipped (age), "
                    f"{excluded} excluded (subdir), {errors} errors")
        return

    # Режим демона с планировщиком
    if daemon_type == 'interval':
        interval = config.get('daemon_interval', 300)
        unit = config.get('daemon_unit', 'seconds')
        logger.info(f"{Colors.BLUE}▶️ Интервальный режим: каждые {interval} {unit}{Colors.END}")

        scheduler = FileScheduler(
            directory=watch_dir,
            rules=rules,
            logger=logger,
            root_allowed=root_allowed,
            subdir_patterns=subdir_patterns,
            min_age_hours=min_age_hours
        )
        scheduler.start_interval(interval)

        logger.info(f"{Colors.GREEN}✅ Сортировщик запущен. Нажмите Ctrl+C для остановки.{Colors.END}")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            if scheduler:
                scheduler.stop()

    elif daemon_type == 'cron':
        cron_expr = config.get('daemon_cron', '0 * * * *')
        logger.info(f"{Colors.BLUE}▶️ Cron-режим: {cron_expr}{Colors.END}")

        scheduler = FileScheduler(
            directory=watch_dir,
            rules=rules,
            logger=logger,
            root_allowed=root_allowed,
            subdir_patterns=subdir_patterns,
            min_age_hours=min_age_hours
        )
        scheduler.start_cron(cron_expr)

        logger.info(f"{Colors.GREEN}✅ Сортировщик запущен. Нажмите Ctrl+C для остановки.{Colors.END}")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            if scheduler:
                scheduler.stop()

    else:  # watchdog mode (по умолчанию)
        logger.info(f"{Colors.BLUE}▶️ Watchdog режим (мгновенная реакция){Colors.END}")

        event_handler = SorterEventHandler(
            rules=rules,
            logger=logger,
            watch_dir=watch_dir,
            root_allowed=root_allowed,
            subdir_patterns=subdir_patterns,
            min_age_hours=min_age_hours
        )

        observer = Observer()
        observer.schedule(event_handler, watch_dir, recursive=False)
        observer.start()

        logger.info(f"{Colors.GREEN}✅ Начат мониторинг папки: {watch_dir}{Colors.END}")
        logger.info(f"{Colors.GREEN}✅ Нажмите Ctrl+C для остановки.{Colors.END}")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            logger.info("🛑 Остановлено пользователем")
        observer.join()


if __name__ == '__main__':
    main()