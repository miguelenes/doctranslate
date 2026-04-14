"""Translation memory (TM) runtime policy types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TMMode(str, Enum):
    """Reuse policy for translation memory beyond legacy exact SQLite cache."""

    OFF = "off"  # Legacy exact cache only (L1); no TM DB reads/writes.
    EXACT = "exact"  # L1 + L1b normalized key lookup in TM DB.
    FUZZY = "fuzzy"  # L1 + L1b + L2 RapidFuzz-gated reuse.
    SEMANTIC = "semantic"  # L1 + L1b + L2 + optional L3 embedding similarity.


class TMScope(str, Enum):
    """Which stored segments are eligible for TM lookup (tightest first)."""

    DOCUMENT = "document"  # Same input file / document id only.
    PROJECT = "project"  # Same project id, then document, then global.
    GLOBAL = "global"  # Any entry matching engine + fingerprint + langs.


@dataclass(frozen=True)
class TMRuntimeConfig:
    """User-facing TM controls (CLI / TranslationConfig)."""

    mode: TMMode = TMMode.OFF
    scope: TMScope = TMScope.DOCUMENT
    min_segment_chars: int = 12
    fuzzy_min_score: float = 92.0
    semantic_min_similarity: float = 0.90
    fuzzy_candidate_limit: int = 800
    cleanup_every_n_writes: int = 500
    max_tm_rows: int = 100_000
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    @staticmethod
    def parse_mode(s: str) -> TMMode:
        try:
            return TMMode(s.lower().strip())
        except ValueError:
            return TMMode.OFF

    @staticmethod
    def parse_scope(s: str) -> TMScope:
        try:
            return TMScope(s.lower().strip())
        except ValueError:
            return TMScope.DOCUMENT
