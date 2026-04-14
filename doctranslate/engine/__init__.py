"""Translation engine orchestration (PDF pipeline entrypoints).

Requires the same optional extras as :mod:`doctranslate.api` (typically ``[full]``).

.. deprecated::
    Prefer :mod:`doctranslate.api` for stable embedding. This package re-exports
    low-level pipeline callables and may overlap with :mod:`doctranslate.pdf`.
"""

from __future__ import annotations

from doctranslate.format.pdf.high_level import async_translate
from doctranslate.format.pdf.high_level import init
from doctranslate.format.pdf.high_level import translate

__all__ = ["async_translate", "init", "translate"]
