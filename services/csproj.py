from __future__ import annotations

import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_NETFX_RE = re.compile(r'^net(\d+)\.(\d+)$')

# Matches both inline and multiline PackageReference elements
_PKG_RE = re.compile(
    r'<PackageReference\b[^>]*/\s*>|<PackageReference\b[^>]*>.*?</PackageReference\s*>',
    re.IGNORECASE | re.DOTALL,
)


def _netfx_version(fw: str) -> tuple[int, int] | None:
    m = _NETFX_RE.match(fw.strip())
    return (int(m.group(1)), int(m.group(2))) if m else None


def _version_tuple(v: str) -> tuple:
    clean = re.sub(r'[-+].*$', '', v.strip())
    try:
        return tuple(int(x) for x in clean.split('.') if x.isdigit())
    except ValueError:
        return (0,)


def _is_upgrade(current: str, target: str) -> bool:
    return _version_tuple(target) > _version_tuple(current)


def _pattern_to_regex(pattern: str) -> re.Pattern:
    escaped = re.escape(pattern).replace(r'\*', '.*')
    return re.compile(f'^{escaped}$', re.IGNORECASE)


def _find_upgrade_version(name: str, upgrades: list, exclusions: list) -> str | None:
    if name.lower() in [e.lower() for e in (exclusions or [])]:
        return None
    for upgrade in (upgrades or []):
        if _pattern_to_regex(upgrade.get('pattern', '')).match(name):
            return upgrade.get('version')
    return None


def _process_content(content: str, config: dict) -> tuple[str, int]:
    """Process a single .csproj/.props file. Returns (new_content, change_count)."""
    source_fw = config.get('source-framework', 'net8.0')
    target_fw = config.get('target-framework', 'net10.0')
    upgrades = config.get('package-upgrades') or []
    exclusions = config.get('package-upgrade-exclusions') or []
    removals = [r.lower() for r in (config.get('package-removals') or [])]

    changes = 0

    # Warn about frameworks below the source version
    src_ver = _netfx_version(source_fw)
    for fw_str in re.findall(r'<TargetFrameworks?>([^<]+)</TargetFrameworks?>', content, re.IGNORECASE):
        for fw in fw_str.split(';'):
            fw_ver = _netfx_version(fw.strip())
            if fw_ver and src_ver and fw_ver < src_ver:
                logger.error(
                    "Project uses %s which is below source framework %s — framework upgrade skipped",
                    fw.strip(), source_fw,
                )

    # Update TargetFramework / TargetFrameworks
    def _replace_fw(m: re.Match) -> str:
        nonlocal changes
        changes += 1
        return m.group(1) + target_fw + m.group(2)

    content = re.sub(
        r'(<TargetFrameworks?>)' + re.escape(source_fw) + r'(</TargetFrameworks?>)',
        _replace_fw,
        content,
        flags=re.IGNORECASE,
    )

    # Process PackageReference elements
    upgraded: set[str] = set()

    def _transform_pkg(m: re.Match) -> str:
        nonlocal changes
        element = m.group(0)

        # Skip Update= elements (only process Include=)
        if re.search(r'\bUpdate=', element, re.IGNORECASE):
            return element

        name_m = re.search(r'\bInclude="([^"]+)"', element, re.IGNORECASE)
        if not name_m:
            return element
        pkg_name = name_m.group(1)

        # Removal
        if pkg_name.lower() in removals:
            changes += 1
            return ''

        # Version (inline attribute or child tag)
        ver_attr = re.search(r'\bVersion="([^"]+)"', element, re.IGNORECASE)
        ver_tag = re.search(r'<Version>([^<]+)</Version>', element, re.IGNORECASE)

        if not ver_attr and not ver_tag:
            return element

        current_ver = (ver_attr or ver_tag).group(1).strip()

        if pkg_name.lower() in upgraded:
            return element

        new_ver = _find_upgrade_version(pkg_name, upgrades, exclusions)
        if not new_ver or not _is_upgrade(current_ver, new_ver):
            return element

        upgraded.add(pkg_name.lower())
        changes += 1

        if ver_attr:
            return re.sub(
                r'(\bVersion=")([^"]+)"',
                rf'\g<1>{new_ver}"',
                element,
                flags=re.IGNORECASE,
            )
        return re.sub(
            r'(<Version>)[^<]+(</Version>)',
            rf'\g<1>{new_ver}\g<2>',
            element,
            flags=re.IGNORECASE,
        )

    content = _PKG_RE.sub(_transform_pkg, content)

    # Clean up blank lines left by removals
    content = re.sub(r'[ \t]+\n', '\n', content)
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content, changes


def upgrade_all_csproj(repo_path: Path, config: dict) -> dict:
    total_changes = 0
    upgraded_files = 0
    processed = 0

    files: list[Path] = [
        *repo_path.rglob('*.csproj'),
        *repo_path.rglob('*.props'),
    ]

    for filepath in files:
        try:
            content = filepath.read_text(encoding='utf-8')
            new_content, changes = _process_content(content, config)
            if changes > 0:
                filepath.write_text(new_content, encoding='utf-8')
                upgraded_files += 1
                total_changes += changes
                logger.info("Updated %s (%d change(s))", filepath, changes)
            processed += 1
        except Exception as e:
            logger.error("Failed to process %s: %s", filepath, e)

    logger.info("Project files: %d processed, %d upgraded", processed, upgraded_files)
    return {
        'changes': total_changes,
        'upgraded_files': upgraded_files,
        'processed': processed,
    }
