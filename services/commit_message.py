import logging
from pathlib import Path

logger = logging.getLogger(__name__)

OUTPUT_FILENAME = 'dotnet-upgrader-code-commit-message'


def write_commit_message(config: dict, count: int, repo_path: Path) -> None:
    template = config.get(
        'commit-message',
        'chore: upgrade .NET from {source} to {target} ({count} project(s))',
    )
    source = config.get('source-framework', 'net8.0')
    target = config.get('target-framework', 'net10.0')

    message = template.format(source=source, target=target, count=count)
    output_path = repo_path / OUTPUT_FILENAME
    output_path.write_text(message, encoding='utf-8')
    logger.info("Commit message written to %s", output_path)
