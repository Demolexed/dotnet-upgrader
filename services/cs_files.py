from __future__ import annotations

import re
import logging
from pathlib import Path

from services.file_utils import find_files

logger = logging.getLogger(__name__)


def process_all_cs_files(repo_path: Path, config: dict) -> dict:
    removals = config.get('code-removals') or []
    if not removals:
        return {'changes': 0, 'processed': 0}

    total_changes = 0
    processed_files = 0

    for removal in removals:
        pattern_str = removal.get('pattern', '')
        file_glob = removal.get('file-glob', '**/*.cs')
        is_regex = removal.get('is-regex', False)

        regex = re.compile(pattern_str if is_regex else re.escape(pattern_str))

        for filepath in find_files(repo_path, file_glob):
            try:
                content = filepath.read_text(encoding='utf-8')
                lines = content.splitlines(keepends=True)
                new_lines = [l for l in lines if not regex.search(l)]
                if len(new_lines) != len(lines):
                    filepath.write_text(''.join(new_lines), encoding='utf-8')
                    removed = len(lines) - len(new_lines)
                    total_changes += removed
                    processed_files += 1
                    logger.info("Removed %d line(s) from %s", removed, filepath)
            except Exception as e:
                logger.error("Failed to process %s: %s", filepath, e)

    return {'changes': total_changes, 'processed': processed_files}
