import argparse
import logging
import time
import sys
import os
import signal
from watchdog.observers import Observer

from .config import load_config
from .config import load_rules
from .logger import setup_logger
from .handlers import SorterEventHandler
from .core import process_all_files
from .scheduler import FileScheduler

# Глобальные переменные для graceful shutdown
scheduler = None
observer = None


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


def main():
    global scheduler, observer

    parser = argparse.ArgumentParser(description="File auto-sorter")
    parser.add_argument('--config', '-c', default='~/.config/dfsort/config.yaml',
                        help='Path to configuration file')
    parser.add_argument('-o', '--once', action='store_true', dest='once',
                        help='Process all existing files and exit')
    parser.add_argument('-d', '--daemon', action='store_true', dest='daemon',
                        help='Run in foreground (for systemd)')
    args = parser.parse_args()

    # Загружаем конфиг
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading config: {e}")
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
        sys.exit(1)

    # Загружаем правила
    rules = load_rules(config)
    logger.info(f"Loaded {len(rules)} rules")

    # Получаем параметры
    min_age_hours = config.get('time_to_move', 0)  # По умолчанию 0 (отключено)
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
        logger.info(f"Once mode: processing all files in {watch_dir}")
        process_all_files(
            directory=watch_dir,
            rules=rules,
            logger=logger,
            root_allowed=root_allowed,
            subdir_patterns=subdir_patterns,
            min_age_hours=min_age_hours
        )
        logger.info("Once mode completed")
        return

    # Режим демона с планировщиком
    if daemon_type == 'interval':
        interval = config.get('daemon_interval', 300)
        unit = config.get('daemon_unit', 'seconds')
        logger.info(f"▶️ Интервальный режим: каждые {interval} {unit}")

        scheduler = FileScheduler(
            directory=watch_dir,
            rules=rules,
            logger=logger,
            root_allowed=root_allowed,
            subdir_patterns=subdir_patterns,
            min_age_hours=min_age_hours
        )
        scheduler.start_interval(interval)

        # Держим программу запущенной
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            if scheduler:
                scheduler.stop()

    elif daemon_type == 'cron':
        cron_expr = config.get('daemon_cron', '0 * * * *')
        logger.info(f"▶️ Cron-режим: {cron_expr}")

        scheduler = FileScheduler(
            directory=watch_dir,
            rules=rules,
            logger=logger,
            root_allowed=root_allowed,
            subdir_patterns=subdir_patterns,
            min_age_hours=min_age_hours
        )
        scheduler.start_cron(cron_expr)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            if scheduler:
                scheduler.stop()

    else:  # watchdog mode (по умолчанию)
        logger.info(f"▶️ Watchdog режим")
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
        logger.info(f"Начат мониторинг папки: {watch_dir}")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            logger.info("Остановлено пользователем")
        observer.join()


if __name__ == '__main__':
    main()