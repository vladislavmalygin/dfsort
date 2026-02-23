import time
import threading
from datetime import datetime
from croniter import croniter


from .core import process_all_files


class FileScheduler:
    """
    Планировщик для периодической сортировки файлов с поддержкой cron-расписаний.
    """

    def __init__(self, directory, rules, logger, root_allowed, subdir_patterns, min_age_hours):
        self.directory = directory
        self.rules = rules
        self.logger = logger
        self.root_allowed = root_allowed
        self.subdir_patterns = subdir_patterns
        self.min_age_hours = min_age_hours
        self.running = False
        self.thread = None

    def run_once(self):
        """Выполняет одну сортировку."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.logger.info(f"🕐 Запуск плановой сортировки в {timestamp}")

        try:
            processed, skipped, errors = process_all_files(
                directory=self.directory,
                rules=self.rules,
                logger=self.logger,
                root_allowed=self.root_allowed,
                subdir_patterns=self.subdir_patterns,
                min_age_hours=self.min_age_hours
            )
            self.logger.info(f"✅ Сортировка завершена: +{processed}, пропущено {skipped}, ошибок {errors}")

        except Exception as e:
            self.logger.error(f"❌ Ошибка при плановой сортировке: {e}")

    def start_interval(self, seconds):
        """Запускает сортировку с фиксированным интервалом."""
        self.logger.info(f"▶️ Интервальный режим: каждые {seconds} секунд")
        self.running = True

        def run():
            while self.running:
                self.run_once()
                # Прогрессивный сон с проверкой флага остановки
                for _ in range(seconds):
                    if not self.running:
                        break
                    time.sleep(1)

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def start_cron(self, cron_expression):
        """
        Запускает сортировку по cron-расписанию.

        Примеры:
        - "0 9 * * 1"      # каждый понедельник в 9:00
        - "0 */2 * * *"     # каждые 2 часа
        - "30 8-20 * * *"   # каждый час с 8:30 до 20:30
        - "0 9 * * 1-5"     # в 9:00 с понедельника по пятницу
        - "0 0 1 * *"       # первого числа каждого месяца в 00:00
        """
        self.logger.info(f"▶️ Cron-режим: {cron_expression}")

        try:
            # Проверяем валидность cron-выражения
            base_time = datetime.now()
            cron = croniter(cron_expression, base_time)
            next_run = cron.get_next(datetime)
            self.logger.info(f"📅 Следующий запуск: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            self.logger.error(f"❌ Неверное cron-выражение: {e}")
            return

        self.running = True

        def run():
            while self.running:
                now = datetime.now()

                # Вычисляем следующий запуск
                cron = croniter(cron_expression, now)
                next_run = cron.get_next(datetime)

                # Сколько секунд до следующего запуска
                wait_seconds = (next_run - now).total_seconds()

                if wait_seconds > 0:
                    self.logger.debug(f"⏳ До следующего запуска: {wait_seconds:.0f} сек")

                    # Спим с проверкой флага остановки
                    for _ in range(int(wait_seconds)):
                        if not self.running:
                            break
                        time.sleep(1)

                    if self.running:
                        self.run_once()

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def stop(self):
        """Останавливает планировщик."""
        self.logger.info("⏹️ Остановка планировщика")
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)