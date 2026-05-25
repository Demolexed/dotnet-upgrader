import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def check_qualifications(repo_path: Path, qualifications: list, config: dict) -> bool:
    for qual in qualifications:
        if not _check(repo_path, qual, config):
            logger.error("Qualification not met: %s", qual)
            return False
    return True


def _check(repo_path: Path, qual: str, config: dict) -> bool:
    if qual == 'has-dotnet-projects':
        return any(repo_path.rglob('*.csproj'))

    if qual == 'has-source-framework':
        source = config.get('source-framework', 'net8.0')
        pattern = re.compile(
            rf'<TargetFrameworks?>{re.escape(source)}</TargetFrameworks?>',
            re.IGNORECASE,
        )
        for f in repo_path.rglob('*.csproj'):
            if pattern.search(f.read_text(encoding='utf-8')):
                return True
        return False

    logger.warning("Unknown qualification '%s' — skipping", qual)
    return True
