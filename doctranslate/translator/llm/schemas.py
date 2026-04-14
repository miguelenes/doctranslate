"""Pydantic models for structured LLM outputs (term extraction, batch translation)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator


class TermPair(BaseModel):
    src: str
    tgt: str


class TermExtractionEnvelope(BaseModel):
    """Root object for term extraction; also accepts a bare JSON list for compatibility."""

    terms: list[TermPair] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _coerce_root_list(cls, data: Any) -> Any:
        if isinstance(data, list):
            return {"terms": data}
        return data


class BatchTranslationItem(BaseModel):
    id: int
    output: str | None = None
    input: str | None = None


class BatchTranslationEnvelope(BaseModel):
    """Batch paragraph translation; accepts bare JSON list for compatibility."""

    items: list[BatchTranslationItem] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _coerce_root_list(cls, data: Any) -> Any:
        if isinstance(data, list):
            return {"items": data}
        return data
