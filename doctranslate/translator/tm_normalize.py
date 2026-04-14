"""Document-oriented normalization for translation memory keys."""

from __future__ import annotations

import hashlib
import re
import unicodedata

# Leading section / list numbering noise (conservative strip once).
_LEADING_ENUM = re.compile(
    r"^\s*(?:"
    r"(?:\(?[ivxlcdm]{1,8}\)?\.)|"  # roman numerals (lowercase)
    r"(?:\d{1,3}(?:\.\d{1,3}){0,4}\.?)|"  # 1. 1.2. 1.2.3.
    r"(?:\([a-z]\)\.?)|"  # (a)
    r"(?:[a-z]\)\.?)"  # a)
    r")\s+",
    re.IGNORECASE,
)

# Full-width punctuation to ASCII-ish (subset common in PDFs).
_FW_MAP = str.maketrans(
    {
        "\u3000": " ",  # ideographic space
        "\uff0c": ",",
        "\u3002": ".",
        "\uff1a": ":",
        "\uff1b": ";",
        "\uff08": "(",
        "\uff09": ")",
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u2013": "-",
        "\u2014": "-",
    },
)

_WS = re.compile(r"\s+")
_PLACEHOLDER_TOKEN = re.compile(
    r"(</?b\d+>|"
    r"\{v\d+\}|"
    r"\{\{\s*\d+\s*\}\}|"
    r"<\s*style\s+id\s*=\s*['\"]\s*\d+\s*['\"]\s*>|"
    r"<\s*/\s*style\s*>)",
    re.IGNORECASE,
)


def stable_hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def normalize_for_tm(text: str, *, lang_in: str = "") -> str:
    """Deterministic normalization for TM keys (not for display).

    Preserves placeholder-like tokens by replacing them with stable markers
    before whitespace collapse so minor placeholder edits still align.
    """
    if not text:
        return ""

    t = unicodedata.normalize("NFKC", text)
    t = t.translate(_FW_MAP)
    # Replace placeholders with canonical markers in order of appearance.
    markers: list[str] = []

    def _sub(m: re.Match) -> str:
        idx = len(markers)
        markers.append(m.group(0))
        return f"\x00PH{idx}\x00"

    t = _PLACEHOLDER_TOKEN.sub(_sub, t)
    t = _LEADING_ENUM.sub("", t, count=1)
    t = _WS.sub(" ", t).strip()
    # CJK: NFKC already helps; avoid aggressive lowercasing for non-Latin.
    li = (lang_in or "").lower()
    if li and not _is_cjk_locale(li):
        t = t.lower()
    return t


def _is_cjk_locale(lang: str) -> bool:
    return any(
        lang.startswith(p) for p in ("zh", "ja", "jp", "ko", "tw", "cn", "hk", "yue")
    )


def placeholder_signature(text: str) -> str:
    """Compact signature of placeholder tokens in order (for safety checks)."""
    found = _PLACEHOLDER_TOKEN.findall(text)
    if not found:
        return ""
    return stable_hash("\n".join(found))[:32]
