import os
import time
from watchdog.events import FileSystemEventHandler

from .core import process_file
from .config import is_subdir_allowed


class SorterEventHandler(FileSystemEventHandler):
    """
    Обработчик событий файловой системы.
    При создании, изменении или перемещении файла вызывает _handle.
    """

    def __init__(self, rules, logger, watch_dir, root_allowed=False, subdir_patterns=None, min_age_hours=0):
        super().__init__()
        self.rules = rules
        self.logger = logger
        self.watch_dir = watch_dir
        self.root_allowed = root_allowed
        self.subdir_patterns = subdir_patterns or []
        self.min_age_seconds = min_age_hours * 3600
        self.processed = set()
        self.logger.debug(f"SorterEventHandler инициализирован: watch_dir={watch_dir}")

    def on_created(self, event):
        if not event.is_directory:
            self.logger.debug(f"Событие created: {event.src_path}")
            self._handle(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.logger.debug(f"Событие modified: {event.src_path}")
            time.sleep(1)  # даём время на завершение записи
            self._handle(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.logger.debug(f"Событие moved: {event.src_path} -> {event.dest_path}")
            # Удаляем старый путь из processed, чтобы обработать новый
            if event.src_path in self.processed:
                self.processed.remove(event.src_path)
            self._handle(event.dest_path)

    def _handle(self, path):
        self.logger.debug(f"Обработка {path}")

        # Проверка существования файла
        if not os.path.exists(path):
            self.logger.debug(f"Файл {path} больше не существует, пропускаем")
            return

        # Проверка на дубликаты
        if path in self.processed:
            self.logger.debug(f"Файл уже обработан: {path}")
            return
        self.processed.add(path)

        # Проверка разрешённой подпапки
        if not is_subdir_allowed(path, self.watch_dir, self.root_allowed, self.subdir_patterns):
            self.logger.debug(f"Файл {path} в неразрешённой подпапке, пропускаем")
            return

        # Проверка возраста файла
        if self.min_age_seconds > 0:
            try:
                file_age = time.time() - os.path.getmtime(path)
                if file_age < self.min_age_seconds:
                    self.logger.debug(f"Файл {path} слишком свежий ({file_age/3600:.1f} ч), пропускаем")
                    return
            except OSError as e:
                self.logger.error(f"Не удалось определить возраст файла {path}: {e}")
                return

        self.logger.info(f"Обнаружен новый файл: {path}")

        try:
            process_file(path, self.rules)
        except Exception as e:
            self.logger.error(f"Ошибка при обработке {path}: {e}")