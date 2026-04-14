"""Filesystem bootstrap without importing the PDF/IL pipeline."""

from __future__ import annotations

import logging
from pathlib import Path

from doctranslate.const import CACHE_FOLDER

logger = logging.getLogger(__name__)


def ensure_user_cache_dirs() -> None:
    """Create the user cache directory tree (same contract as :func:`format.pdf.high_level.init`)."""
    try:
        logger.debug("create cache folder at %s", CACHE_FOLDER)
        Path(CACHE_FOLDER).mkdir(parents=True, exist_ok=True)
    except OSError:
        logger.critical(
            "Failed to create cache folder at %s",
            CACHE_FOLDER,
            exc_info=True,
        )
        raise SystemExit(1) from None
