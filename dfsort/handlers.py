import time
from watchdog.events import FileSystemEventHandler

from .core import process_file

class SorterEventHandler(FileSystemEventHandler):
    """
    Обработчик событий файловой системы.
    При создании или изменении файла вызывает _handle.
    """

    def __init__(self, rules, logger, min_age_hours=0):
        super().__init__()
        self.rules = rules
        self.logger = logger
        self.min_age_seconds = min_age_hours * 3600
        self.processed = set()

    def on_created(self, event):
        if not event.is_directory:
            self._handle(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            time.sleep(5)
            self._handle(event.src_path)

    def _handle(self, path):
        if path in self.processed:
            return
        self.processed.add(path)

        self.logger.info(f"Обнаружен новый файл: {path}")

        try:
            process_file(path, self.rules)
        except Exception as e:
            self.logger.error(f"Error processing {path}: {e}")

