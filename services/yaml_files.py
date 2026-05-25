from __future__ import annotations

import re
import logging
from pathlib import Path

from services.file_utils import find_files

logger = logging.getLogger(__name__)


def process_all_yaml_files(repo_path: Path, config: dict) -> dict:
    replacements = config.get('yaml-replacements') or []
    if not replacements:
        return {'changes': 0, 'processed': 0}

    return _apply_replacements(repo_path, replacements, '**/*.yml')


def _apply_replacements(repo_path: Path, replacements: list, default_glob: str) -> dict:
    total_changes = 0
    processed_files = 0

    for repl in replacements:
        pattern_str = repl.get('pattern', '')
        replacement = repl.get('replacement', '')
        file_glob = repl.get('file-glob', default_glob)
        is_regex = repl.get('is-regex', False)

        regex = re.compile(pattern_str if is_regex else re.escape(pattern_str))

        for filepath in find_files(repo_path, file_glob):
            try:
                content = filepath.read_text(encoding='utf-8')
                new_content, n = regex.subn(replacement, content)
                if n > 0:
                    filepath.write_text(new_content, encoding='utf-8')
                    total_changes += n
                    processed_files += 1
                    logger.info("Applied %d replacement(s) in %s", n, filepath)
            except Exception as e:
                logger.error("Failed to process %s: %s", filepath, e)

    return {'changes': total_changes, 'processed': processed_files}
