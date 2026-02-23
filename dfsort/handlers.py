import time
from watchdog.events import FileSystemEventHandler

class SorterEventHandler(FileSystemEventHandler):
    """
    Обработчик событий файловой системы.
    При создании или изменении файла вызывает _handle.
    """
    def __init__(self, logger):
        super().__init__()
        self.logger = logger
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

        # Будущая сортировка
        # process_file(path, ...)

        # Будущее удаление записей
