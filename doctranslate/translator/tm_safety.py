"""Safety gates for translation memory fuzzy / semantic reuse."""

from __future__ import annotations

import logging
import re

from doctranslate.translator.tm_normalize import placeholder_signature

logger = logging.getLogger(__name__)


def segment_long_enough(text: str, min_chars: int) -> bool:
    if min_chars <= 0:
        return True
    stripped = text.strip()
    return len(stripped) >= min_chars


def placeholders_compatible(source: str, candidate_source: str, target: str) -> bool:
    """Require same placeholder signature between query and stored source."""
    a = placeholder_signature(source)
    b = placeholder_signature(candidate_source)
    if a != b:
        return False
    # If placeholders exist, target should contain same marker count roughly
    # (same PH markers in normalized sense is already enforced by a==b on sources).
    _ = target
    return True


def glossary_compatible(
    source_text: str,
    candidate_translation: str,
    glossary_pairs: list[tuple[str, str]],
) -> bool:
    """If a glossary source term appears in ``source_text``, require target substring."""
    if not glossary_pairs:
        return True
    for src_term, tgt_term in glossary_pairs:
        if not src_term or not tgt_term:
            continue
        if src_term in source_text and tgt_term not in candidate_translation:
            logger.debug(
                "TM glossary check failed: source contains %r but translation "
                "missing target %r",
                src_term[:80],
                tgt_term[:80],
            )
            return False
    return True


def token_count_approx(text: str) -> int:
    """Rough token count for min-length policy (whitespace split + CJK chars)."""
    if not text:
        return 0
    # Count CJK codepoints as separate tokens.
    cjk = len(re.findall(r"[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff]", text))
    latin = len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text))
    spaces = len(text.split())
    return max(cjk, latin, spaces)
