import logging
from pathlib import Path

from services.yaml_files import _apply_replacements

logger = logging.getLogger(__name__)


def process_all_dockerfiles(repo_path: Path, config: dict) -> dict:
    replacements = config.get('dockerfile-replacements') or []
    if not replacements:
        return {'changes': 0, 'processed': 0}

    return _apply_replacements(repo_path, replacements, 'Dockerfile')
