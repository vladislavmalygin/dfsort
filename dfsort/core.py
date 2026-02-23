import logging
from .actions import move_file, extract_archive

logger = logging.getLogger('dfsort')

def process_file(filepath, rules):
    """
    Применяет правила к файлу.
    Выполняет действие первого подходящего правила.
    """
    logger.info(f"process_file called for {filepath}")
    for rule in rules:
        if rule.matches(filepath):
            logger.info(f"Rule '{rule.name}' matched for {filepath}")
            try:
                if rule.action == 'move':
                    move_file(filepath, rule.destination,
                              conflict=rule.conflict,
                              subfolder_by_date=rule.subfolder_by_date)
                elif rule.action == 'extract':
                    extract_archive(filepath, rule.destination,
                                    conflict=rule.conflict)
                else:
                    logger.warning(f"Unknown action {rule.action} in rule '{rule.name}'")
            except Exception as e:
                logger.error(f"Failed to apply rule '{rule.name}' to {filepath}: {e}")
            return
    logger.debug(f"No rule matched for {filepath}")