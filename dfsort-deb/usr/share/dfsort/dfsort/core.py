import os
import time
import logging
from .actions import move_file, extract_archive, delete_file
from .config import is_subdir_allowed

logger = logging.getLogger('dfsort')

def process_file(filepath, rules):
    """
    Применяет правила к файлу.
    """
    logger.info(f"process_file called for {filepath}")
    for rule in rules:
        if rule.matches(filepath):
            logger.info(f"Rule '{rule.name}' matched for {filepath}")
            try:
                if rule.action == 'move':
                    logger.info(f"Moving to {rule.destination}")
                    move_file(filepath, rule.destination,
                              conflict=rule.conflict,
                              subfolder_by_date=rule.subfolder_by_date)
                elif rule.action == 'extract':
                    logger.info(f"Extracting to {rule.destination}")
                    extract_archive(filepath, rule.destination,
                                    conflict=rule.conflict)
                elif rule.action == 'delete':
                    logger.info(f"Deleting file")
                    delete_file(filepath)
                else:
                    logger.warning(f"Unknown action {rule.action} in rule '{rule.name}'")
                return True
            except Exception as e:
                logger.error(f"Failed to apply rule '{rule.name}' to {filepath}: {e}")
                return False
    logger.debug(f"No rule matched for {filepath}")
    return False

def process_all_files(directory, rules, logger, root_allowed=False, subdir_patterns=None, min_age_hours=0):
    """
    Рекурсивно обходит директорию и обрабатывает только файлы в разрешённых подпапках.
    Возвращает кортеж (processed, skipped, excluded, errors)
    """
    subdir_patterns = subdir_patterns or []
    min_age_seconds = min_age_hours * 3600
    processed_count = 0
    skipped_count = 0
    excluded_count = 0
    error_count = 0

    logger.info(f"Starting process_all_files in {directory}")
    logger.info(f"root_allowed: {root_allowed}")
    logger.info(f"subdir_patterns: {[p.pattern for p in subdir_patterns]}")
    logger.info(f"min_age_hours: {min_age_hours}")

    for root, dirs, files in os.walk(directory):
        # Пропускаем скрытые папки
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for filename in files:
            filepath = os.path.join(root, filename)

            # Пропускаем скрытые файлы
            if filename.startswith('.'):
                continue

            # Проверка разрешённых подпапок
            if not is_subdir_allowed(filepath, directory, root_allowed, subdir_patterns):
                logger.debug(f"File {filepath} in non-allowed subdirectory, skipping")
                excluded_count += 1
                continue

            # Проверка возраста
            if min_age_seconds > 0:
                try:
                    file_age = time.time() - os.path.getmtime(filepath)
                    if file_age < min_age_seconds:
                        logger.debug(f"File {filepath} too young ({file_age/3600:.1f} hours), skipping")
                        skipped_count += 1
                        continue
                except OSError as e:
                    logger.error(f"Cannot get age of {filepath}: {e}")
                    error_count += 1
                    continue

            try:
                process_file(filepath, rules)
                processed_count += 1
            except Exception as e:
                logger.error(f"Error processing {filepath}: {e}")
                error_count += 1

    logger.info(f"Once mode summary: {processed_count} processed, {skipped_count} skipped (age), {excluded_count} excluded (subdir), {error_count} errors")
    return processed_count, skipped_count, excluded_count, error_count