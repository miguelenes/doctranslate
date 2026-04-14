"""Shared job input validation (mounted paths)."""

from __future__ import annotations

from pathlib import Path

from doctranslate.schemas.enums import PublicErrorCode
from doctranslate.schemas.public_api import TranslationErrorPayload


def _is_under_allowed_prefix(path: Path, prefixes: list[str]) -> bool:
    try:
        resolved = path.expanduser().resolve()
    except OSError:
        return False
    for raw in prefixes:
        try:
            base = Path(raw).expanduser().resolve()
        except OSError:
            continue
        try:
            resolved.relative_to(base)
            return True
        except ValueError:
            continue
    return False


def validate_mounted_input(
    path: Path,
    *,
    allow_mounted_paths: bool,
    mounted_allow_prefixes: list[str],
) -> TranslationErrorPayload | None:
    """Return an error payload if mounted path input is invalid; else None."""
    if not allow_mounted_paths:
        return TranslationErrorPayload(
            code=PublicErrorCode.UNSUPPORTED_CONFIGURATION,
            message="Mounted path input is disabled by server policy.",
            retryable=False,
        )
    if not path.is_file():
        return TranslationErrorPayload(
            code=PublicErrorCode.NOT_FOUND,
            message=f"Input PDF not found: {path}",
            retryable=False,
        )
    if not _is_under_allowed_prefix(path, mounted_allow_prefixes):
        return TranslationErrorPayload(
            code=PublicErrorCode.VALIDATION_ERROR,
            message="Input path is not under an allowed mount prefix.",
            retryable=False,
            details={
                "path": str(path),
                "allowed_prefixes": mounted_allow_prefixes,
            },
        )
    return None
