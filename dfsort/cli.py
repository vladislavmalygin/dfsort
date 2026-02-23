import argparse
import logging
import time
import sys
import os
from watchdog.observers import Observer

from .config import load_config
from .config import load_rules
from .logger import setup_logger
from .handlers import SorterEventHandler
from .core import process_all_files

def main():
    parser = argparse.ArgumentParser(description="File auto-sorter")
    parser.add_argument('--config', '-c', default='~/.config/dfsort/config.yaml',
                        help='Path to configuration file')
    parser.add_argument('-o', '--once', action='store_true', dest='once',
                        help='Process all existing files and exit')
    parser.add_argument('-d', '--daemon', action='store_true', dest='daemon',
                        help='Run in foreground (for systemd)')
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

    log_file = config.get('logging', {}).get('file')
    log_level = config.get('logging', {}).get('level', 'INFO')
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger = setup_logger(log_file, numeric_level)

    watch_dir = config.get('watch_directory')
    if not watch_dir:
        logger.error("watch_directory not specified in config")
        sys.exit(1)

    if not os.path.isdir(watch_dir):
        logger.error(f"Watch directory does not exist: {watch_dir}")
        sys.exit(1)

    rules = load_rules(config)
    logger.info(f"Loaded {len(rules)} rules")

    min_age_hours = config.get('time_to_move', 1)
    if min_age_hours:
        logger.info(f"Files will be processed only after {min_age_hours} hours")

    if args.once:
        logger.info(f"Once mode: processing all files in {watch_dir}")
        process_all_files(watch_dir, rules, logger, min_age_hours)
        logger.info("Once mode completed")
        return

    event_handler = SorterEventHandler(
        rules=rules,
        logger=logger,
        watch_dir=watch_dir,
        root_allowed=config.get('root_allowed', False),
        subdir_patterns=config.get('subdir_patterns', []),
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