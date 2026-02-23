import re
import magic
import os
import logging

class Rule:
    def __init__(self, rule_dict):
        self.name = rule_dict.get('name', 'Unnamed')
        self.patterns = rule_dict.get('patterns', [])
        self.mime_patterns = rule_dict.get('mime_types', [])
        self.destination = rule_dict.get('destination')
        self.action = rule_dict.get('action', 'move')
        self.conflict = rule_dict.get('conflict', 'rename')
        self.subfolder_by_date = rule_dict.get('subfolder_by_date')

        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.patterns]
        self.compiled_mime = [re.compile(m, re.IGNORECASE) for m in self.mime_patterns]

    def matches(self, filepath):
        """
        Проверяет, подходит ли файл под правило.
        Сначала проверяем по имени файла (regex), затем по MIME-типу.
        """
        filename = os.path.basename(filepath)

        for pattern in self.compiled_patterns:
            if pattern.search(filename):
                return True

        if self.compiled_mime:
            try:
                mime = magic.from_file(filepath, mime=True)
                logger.debug(f"MIME type of {filepath}: {mime}")
                for pattern in self.compiled_mime:
                    if pattern.search(mime):
                        return True
            except Exception as e:
                pass

        return False