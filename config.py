import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open(encoding='utf-8') as f:
        raw = yaml.safe_load(f)
    cfg = (raw or {}).get('dotnet-upgrader', {})
    logger.debug("Config loaded from %s", path)
    return cfg or {}
