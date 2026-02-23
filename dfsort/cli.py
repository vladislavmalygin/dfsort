# dfsort/cli.py
import argparse
import logging
import time
import sys
import os
from watchdog.observers import Observer

from .config import load_config, load_rules
from .logger import setup_logger
from .handlers import SorterEventHandler

def main():
    parser = argparse.ArgumentParser(description="File auto-sorter")
    parser.add_argument('--config', '-c', default='~/.config/dfsort/config.yaml',
                        help='Path to configuration file')
    parser.add_argument('-o', '--once', action='store_true', dest='once',
                        help='Process all existing files and exit (to be developed)')
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
    logger.setLevel(logging.DEBUG)

    watch_dir = config.get('watch_directory')
    if not watch_dir:
        logger.error("watch_directory not specified in config")
        sys.exit(1)

    if not os.path.isdir(watch_dir):
        logger.error(f"Watch directory does not exist: {watch_dir}")
        sys.exit(1)

    rules = load_rules(config)
    logger.info(f"Loaded {len(rules)} rules")

    if args.once:
        logger.info("Once mode is not yet implemented. Exiting.")
        return

    event_handler = SorterEventHandler(rules, logger)
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