from __future__ import annotations

from pathlib import Path


def find_files(root: Path, file_glob: str) -> list[Path]:
    """Find files recursively under root matching a glob pattern."""
    pattern = file_glob.lstrip('/')
    if pattern.startswith('**/'):
        pattern = pattern[3:]
    return list(root.rglob(pattern))
