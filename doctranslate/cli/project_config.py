"""Load project TOML defaults for CLI (vNext)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import toml

logger = logging.getLogger(__name__)


def load_flat_doctranslate_defaults(path: Path) -> dict[str, Any]:
    """Return flat key/value dict from scalar keys under ``[doctranslate]``."""
    if not path.is_file():
        return {}
    raw = toml.load(path)
    if not isinstance(raw, dict):
        return {}
    out: dict[str, Any] = {}
    doc = raw.get("doctranslate")
    if isinstance(doc, dict):
        for k, v in doc.items():
            if isinstance(v, dict):
                continue
            out[k] = v
    return out


def load_profile_overlay(path: Path, profile: str) -> dict[str, Any]:
    """Load ``[profiles.<name>]`` or ``[doctranslate.profiles.<name>]`` as flat scalars."""
    if not path.is_file() or not profile:
        return {}
    raw = toml.load(path)
    if not isinstance(raw, dict):
        return {}
    prof = raw.get("profiles", {}).get(profile)
    if isinstance(prof, dict):
        return {k: v for k, v in prof.items() if not isinstance(v, dict)}
    nested = raw.get("doctranslate", {})
    if isinstance(nested, dict):
        prof2 = nested.get("profiles", {}).get(profile)
        if isinstance(prof2, dict):
            return {k: v for k, v in prof2.items() if not isinstance(v, dict)}
    return {}
