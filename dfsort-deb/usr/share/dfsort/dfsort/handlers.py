import os
import time
from watchdog.events import FileSystemEventHandler

from .core import process_file
from .config import is_subdir_allowed


class SorterEventHandler(FileSystemEventHandler):
    """
    Обработчик событий файловой системы.
    При создании или изменении файла вызывает _handle.
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

        # Отладка: выведем параметры при инициализации
        self.logger.debug(f"=== SorterEventHandler инициализирован ===")
        self.logger.debug(f"watch_dir: {watch_dir}")
        self.logger.debug(f"root_allowed: {root_allowed}")
        self.logger.debug(f"subdir_patterns: {[p.pattern for p in subdir_patterns] if subdir_patterns else []}")
        self.logger.debug(f"min_age_hours: {min_age_hours}")

    def on_created(self, event):
        if not event.is_directory:
            self.logger.debug(f"Событие created: {event.src_path}")
            self._handle(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.logger.debug(f"Событие modified: {event.src_path}")
            time.sleep(5)
            self._handle(event.src_path)

    def _handle(self, path):
        self.logger.debug(f"=== _handle вызван для {path} ===")

        # Проверка на дубликаты
        if path in self.processed:
            self.logger.debug(f"Файл уже обработан: {path}")
            return
        self.processed.add(path)
        self.logger.debug(f"Файл добавлен в processed")

        # Проверка, находится ли файл в разрешённой подпапке
        self.logger.debug(f"Вызываем is_subdir_allowed с параметрами:")
        self.logger.debug(f"  path: {path}")
        self.logger.debug(f"  watch_dir: {self.watch_dir}")
        self.logger.debug(f"  root_allowed: {self.root_allowed}")
        self.logger.debug(f"  subdir_patterns: {[p.pattern for p in self.subdir_patterns]}")

        allowed = is_subdir_allowed(path, self.watch_dir, self.root_allowed, self.subdir_patterns)
        self.logger.debug(f"is_subdir_allowed вернул: {allowed}")

        if not allowed:
            self.logger.debug(f"Файл {path} в неразрешённой подпапке, пропускаем")
            return

        # Проверка возраста файла
        if self.min_age_seconds > 0:
            try:
                file_age = time.time() - os.path.getmtime(path)
                self.logger.debug(f"Возраст файла: {file_age} сек, минимум: {self.min_age_seconds} сек")
                if file_age < self.min_age_seconds:
                    self.logger.debug(f"Файл {path} слишком свежий ({file_age / 3600:.1f} ч), пропускаем")
                    return
            except OSError as e:
                self.logger.error(f"Не удалось определить возраст файла {path}: {e}")
                return

        self.logger.info(f"Обнаружен новый файл: {path}")

        try:
            self.logger.debug(f"Вызываем process_file для {path}")
            process_file(path, self.rules)
        except Exception as e:
            self.logger.error(f"Error processing {path}: {e}")