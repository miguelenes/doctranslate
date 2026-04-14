"""Optional semantic (embedding) backend for translation memory L3."""

from __future__ import annotations

import logging
import struct
from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING

import numpy as np

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass


class SemanticBackend(ABC):
    """Encode text to float32 vectors for cosine similarity."""

    @property
    def available(self) -> bool:
        return True

    @property
    def dimension(self) -> int:
        return 0

    @abstractmethod
    def encode(self, texts: list[str]) -> np.ndarray:
        """Return float32 array shape (n, d)."""


class NullSemanticBackend(SemanticBackend):
    """Placeholder when sentence-transformers is not installed."""

    @property
    def available(self) -> bool:
        return False

    @property
    def dimension(self) -> int:
        return 0

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.zeros((len(texts), 0), dtype=np.float32)


class SentenceTransformerBackend(SemanticBackend):
    """Local embeddings via sentence-transformers (optional dependency)."""

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)
        self._dim = int(self._model.get_sentence_embedding_dimension())

    @property
    def available(self) -> bool:
        return True

    @property
    def dimension(self) -> int:
        return self._dim

    def encode(self, texts: list[str]) -> np.ndarray:
        emb = self._model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        out = np.asarray(emb, dtype=np.float32)
        if out.ndim == 1:
            out = out.reshape(1, -1)
        return out


def try_create_semantic_backend(model_name: str) -> SemanticBackend:
    """Return a working backend or ``NullSemanticBackend``."""
    try:
        be = SentenceTransformerBackend(model_name)
        logger.info("TM semantic backend loaded: %s (dim=%s)", model_name, be.dimension)
        return be
    except Exception:
        logger.debug(
            "TM semantic backend unavailable (install sentence-transformers + torch): ",
            exc_info=True,
        )
        return NullSemanticBackend()


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two 1-d float32 vectors."""
    if a.size == 0 or b.size == 0:
        return 0.0
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def serialize_embedding_f32(vec: np.ndarray) -> bytes:
    v = np.asarray(vec, dtype=np.float32).flatten()
    return struct.pack(f"{v.size}f", *v.tolist())


def deserialize_embedding_f32(blob: bytes) -> np.ndarray:
    n = len(blob) // 4
    return np.array(struct.unpack(f"{n}f", blob), dtype=np.float32)
