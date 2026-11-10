"""Module discovery via entry points (TASK-070)."""

from __future__ import annotations

import importlib.metadata
import logging
import re

from app.core.module_key import is_valid_module_key
from app.modules.contract import ModuleManifest

logger = logging.getLogger(__name__)

# The module contract's version rule (SR-016 AC 1): the semver.org expression, ASCII only.
# Always use ``fullmatch``.
_NUMERIC = r"(?:0|[1-9][0-9]*)"
_PRE_ID = rf"(?:{_NUMERIC}|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*)"
_BUILD_ID = r"[0-9a-zA-Z-]+"
_SEMVER_RE = re.compile(
    rf"{_NUMERIC}\.{_NUMERIC}\.{_NUMERIC}"
    rf"(?:-{_PRE_ID}(?:\.{_PRE_ID})*)?"
    rf"(?:\+{_BUILD_ID}(?:\.{_BUILD_ID})*)?",
    re.ASCII,
)


def _is_valid_manifest(manifest: object) -> bool:
    """Return True if manifest satisfies the ModuleManifest contract."""
    module_key = getattr(manifest, "module_key", None)
    name = getattr(manifest, "name", None)
    version = getattr(manifest, "version", None)
    required_permissions = getattr(manifest, "required_permissions", None)

    if not module_key or not isinstance(module_key, str):
        logger.warning("Manifest rejected: module_key missing or empty (%.80r)", module_key)
        return False
    if not is_valid_module_key(module_key):
        logger.warning("Manifest rejected: module_key not a valid key (%.80r)", module_key)
        return False
    if not name or not isinstance(name, str):
        logger.warning("Manifest rejected: name missing or empty (%.80r)", name)
        return False
    if not version or not isinstance(version, str) or not _SEMVER_RE.fullmatch(version):
        logger.warning(
            "Manifest rejected: version not valid (%.80r, length %d)",
            version,
            len(version) if isinstance(version, str) else 0,
        )
        return False
    if not isinstance(required_permissions, list):
        logger.warning(
            "Manifest rejected: required_permissions not a list (%r)", required_permissions
        )
        return False
    return True


def discover_modules() -> list[ModuleManifest]:
    """Load all manifests from the 'medhub.modules' entry point group.

    Per-module errors are isolated — a single bad module does not abort discovery.
    """
    manifests: list[ModuleManifest] = []
    eps = importlib.metadata.entry_points(group="medhub.modules")
    for ep in eps:
        try:
            manifest = ep.load()
        except Exception:
            logger.exception("Failed to load module entry point %r — skipping", ep.name)
            continue
        if not _is_valid_manifest(manifest):
            continue
        manifests.append(manifest)
        logger.info("Discovered module %r v%s", manifest.module_key, manifest.version)
    return manifests
