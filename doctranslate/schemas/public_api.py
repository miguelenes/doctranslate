"""Stable public request/result/progress/error models (Pydantic v2).

These types are the cross-repo contract. Runtime classes such as
:class:`~doctranslate.format.pdf.translation_config.TranslationConfig` are internal.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Annotated
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

from doctranslate.schemas.enums import ArtifactKind
from doctranslate.schemas.enums import ProgressEventType
from doctranslate.schemas.enums import PublicErrorCode
from doctranslate.schemas.enums import TranslatorMode
from doctranslate.schemas.versions import PROGRESS_EVENT_VERSION
from doctranslate.schemas.versions import PUBLIC_SCHEMA_VERSION


class TranslationMemorySpec(BaseModel):
    """Translation memory options (maps to :class:`~doctranslate.format.pdf.translation_settings.TranslationSettings` TM fields)."""

    model_config = ConfigDict(extra="forbid")

    tm_mode: Literal["off", "exact", "fuzzy", "semantic"] = "off"
    tm_scope: Literal["document", "project", "global"] = "document"
    tm_min_segment_chars: int = 12
    tm_fuzzy_min_score: float = 92.0
    tm_semantic_min_similarity: float = 0.90
    tm_project_id: str = ""
    tm_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    tm_import_path: str | None = None
    tm_export_path: str | None = None


class GlossaryEntrySpec(BaseModel):
    """Single glossary row (optional inline glossaries)."""

    model_config = ConfigDict(extra="forbid")

    source: str
    target: str
    target_language: str | None = Field(
        default=None,
        description="Optional tgt_lng column equivalent for filtering.",
    )


class GlossarySpec(BaseModel):
    """User glossary inputs: CSV paths and/or inline entries."""

    model_config = ConfigDict(extra="forbid")

    csv_paths: list[str] = Field(default_factory=list)
    inline_name: str = "inline_glossary"
    inline_entries: list[GlossaryEntrySpec] = Field(default_factory=list)


class OpenAIRequestArgs(BaseModel):
    """Arguments for legacy OpenAI translator construction."""

    model_config = ConfigDict(extra="forbid")

    model: str = "gpt-4o-mini"
    base_url: str | None = None
    api_key: str | None = None
    enable_json_mode_if_requested: bool = False
    send_dashscope_header: bool = False
    send_temperature: bool = True
    reasoning: str | None = None
    term_model: str | None = None
    term_base_url: str | None = None
    term_api_key: str | None = None
    term_reasoning: str | None = None


class TranslatorRequestConfig(BaseModel):
    """How to build translators for a job."""

    model_config = ConfigDict(extra="forbid")

    mode: TranslatorMode = TranslatorMode.OPENAI
    config_path: str | None = None
    ignore_cache: bool = False
    openai: OpenAIRequestArgs | None = None
    cli_router_overrides: dict[str, Any] | None = None
    local_cli: dict[str, Any] | None = None


class TranslationOptions(BaseModel):
    """PDF/runtime options (optional; defaults match engine defaults)."""

    model_config = ConfigDict(extra="forbid")

    pages: str | None = None
    output_dir: str | None = None
    working_dir: str | None = None
    debug: bool = False
    no_dual: bool = False
    no_mono: bool = False
    qps: int = 4
    report_interval: float = 0.1
    watermark_output_mode: Literal["watermarked", "no_watermark", "both"] = (
        "watermarked"
    )
    glossary: GlossarySpec | None = None
    translation_memory: TranslationMemorySpec | None = None
    ocr_mode: Literal["off", "auto", "force", "hybrid"] = "off"
    ocr_pages: str | None = None
    ocr_lang_hints: list[str] = Field(default_factory=list)
    ocr_debug_dump: bool = False
    auto_extract_glossary: bool = True
    skip_translation: bool = False
    only_parse_generate_pdf: bool = False
    pool_max_workers: int | None = None
    term_pool_max_workers: int | None = None
    llm_translation_batch_max_tokens: int | None = None
    llm_translation_batch_max_paragraphs: int | None = None
    llm_term_extraction_batch_max_tokens: int | None = None
    llm_term_extraction_batch_max_paragraphs: int | None = None
    max_pages_per_part: int | None = None
    use_rich_pbar: bool = True
    metadata_extra_data: str | None = None


class TranslationRequest(BaseModel):
    """Stable, versioned request to run one PDF translation job."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(
        default=PUBLIC_SCHEMA_VERSION,
        description="Client-declared schema version; must match supported version.",
    )
    input_pdf: str = Field(description="Path to the input PDF.")
    lang_in: str = "en"
    lang_out: str = "zh"
    translator: TranslatorRequestConfig = Field(
        default_factory=lambda: TranslatorRequestConfig(mode=TranslatorMode.OPENAI),
    )
    options: TranslationOptions | None = None

    @model_validator(mode="after")
    def _check_schema_version(self) -> TranslationRequest:
        if self.schema_version != PUBLIC_SCHEMA_VERSION:
            msg = f"Unsupported schema_version {self.schema_version!r}; supported: {PUBLIC_SCHEMA_VERSION!r}"
            raise ValueError(msg)
        return self


class TranslationErrorPayload(BaseModel):
    """Structured error for API/CLI consumers."""

    model_config = ConfigDict(extra="forbid")

    code: PublicErrorCode
    message: str
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class ArtifactDescriptor(BaseModel):
    """One output artifact."""

    model_config = ConfigDict(extra="forbid")

    kind: ArtifactKind
    path: str
    sha256: str | None = None
    size_bytes: int | None = None
    media_type: str | None = None
    schema_version: str = PUBLIC_SCHEMA_VERSION


class ArtifactManifest(BaseModel):
    """All artifacts from a completed job."""

    model_config = ConfigDict(extra="forbid")

    items: list[ArtifactDescriptor] = Field(default_factory=list)


class TranslationSummary(BaseModel):
    """High-level run metrics."""

    model_config = ConfigDict(extra="forbid")

    original_pdf_path: str
    total_seconds: float | None = None
    peak_memory_usage_mb: float | None = None
    total_valid_character_count: int | None = None
    total_valid_text_token_count: int | None = None


class TranslationResult(BaseModel):
    """Stable completion payload (replaces ad hoc TranslateResult for embedders)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = PUBLIC_SCHEMA_VERSION
    summary: TranslationSummary
    artifacts: ArtifactManifest
    warnings: list[str] = Field(default_factory=list)


class InputFileInspection(BaseModel):
    """Per-file PDF inspection (no translation)."""

    model_config = ConfigDict(extra="forbid")

    path: str
    page_count: int
    prior_translated_marker: bool | None = None


class InputInspectionResult(BaseModel):
    """Result of :func:`doctranslate.api.inspect_input`."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = PUBLIC_SCHEMA_VERSION
    files: list[InputFileInspection] = Field(default_factory=list)


class StageWeight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    percent: float


class StageSummaryEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal[ProgressEventType.STAGE_SUMMARY] = ProgressEventType.STAGE_SUMMARY
    schema_version: str = PUBLIC_SCHEMA_VERSION
    event_version: str = PROGRESS_EVENT_VERSION
    stages: list[StageWeight]
    part_index: int | None = None
    total_parts: int | None = None


class ProgressStartEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal[ProgressEventType.PROGRESS_START] = ProgressEventType.PROGRESS_START
    schema_version: str = PUBLIC_SCHEMA_VERSION
    event_version: str = PROGRESS_EVENT_VERSION
    stage: str
    stage_progress: float
    stage_current: int
    stage_total: int
    overall_progress: float | None = Field(default=None)
    part_index: int | None = None
    total_parts: int | None = None


class ProgressUpdateEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal[ProgressEventType.PROGRESS_UPDATE] = ProgressEventType.PROGRESS_UPDATE
    schema_version: str = PUBLIC_SCHEMA_VERSION
    event_version: str = PROGRESS_EVENT_VERSION
    stage: str
    stage_progress: float
    stage_current: int
    stage_total: int
    overall_progress: float
    part_index: int | None = None
    total_parts: int | None = None


class ProgressEndEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal[ProgressEventType.PROGRESS_END] = ProgressEventType.PROGRESS_END
    schema_version: str = PUBLIC_SCHEMA_VERSION
    event_version: str = PROGRESS_EVENT_VERSION
    stage: str
    stage_progress: float
    stage_current: int
    stage_total: int
    overall_progress: float | None = Field(default=None)
    part_index: int | None = None
    total_parts: int | None = None


class TranslationFinishedEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal[ProgressEventType.FINISH] = ProgressEventType.FINISH
    schema_version: str = PUBLIC_SCHEMA_VERSION
    event_version: str = PROGRESS_EVENT_VERSION
    translation_result: TranslationResult


class TranslationErrorEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal[ProgressEventType.ERROR] = ProgressEventType.ERROR
    schema_version: str = PUBLIC_SCHEMA_VERSION
    event_version: str = PROGRESS_EVENT_VERSION
    error: TranslationErrorPayload


ProgressEvent = Annotated[
    StageSummaryEvent
    | ProgressStartEvent
    | ProgressUpdateEvent
    | ProgressEndEvent
    | TranslationFinishedEvent
    | TranslationErrorEvent,
    Field(discriminator="type"),
]


class CliJsonEnvelope(BaseModel):
    """Unified stdout envelope for ``--output-format json`` (commands and translate stream final line)."""

    model_config = ConfigDict(extra="forbid")

    ok: bool
    schema_version: str = PUBLIC_SCHEMA_VERSION
    command: str = ""
    stream: Literal["final"] = "final"
    result: dict[str, Any] | TranslationResult | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[TranslationErrorPayload] = Field(default_factory=list)
    error: TranslationErrorPayload | None = None


class CliProgressLine(BaseModel):
    """One NDJSON line for ``--emit-progress-json`` during translate."""

    model_config = ConfigDict(extra="forbid")

    stream: Literal["progress"] = "progress"
    schema_version: str = PUBLIC_SCHEMA_VERSION
    command: str = "translate"
    event: dict[str, Any]


def progress_event_from_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Validate/normalize a raw engine progress dict into the public event shape.

    Returns a JSON-friendly dict (validated via Pydantic).
    """
    t = data.get("type")
    base = {
        "schema_version": PUBLIC_SCHEMA_VERSION,
        "event_version": PROGRESS_EVENT_VERSION,
    }
    if t == ProgressEventType.STAGE_SUMMARY:
        merged = {**base, **data}
        ev = StageSummaryEvent.model_validate(merged)
        return ev.model_dump(mode="json")
    if t == ProgressEventType.PROGRESS_START:
        merged = {**base, **data}
        ev = ProgressStartEvent.model_validate(merged)
        return ev.model_dump(mode="json")
    if t == ProgressEventType.PROGRESS_UPDATE:
        merged = {**base, **data}
        ev = ProgressUpdateEvent.model_validate(merged)
        return ev.model_dump(mode="json")
    if t == ProgressEventType.PROGRESS_END:
        merged = {**base, **data}
        ev = ProgressEndEvent.model_validate(merged)
        return ev.model_dump(mode="json")
    if t == ProgressEventType.FINISH:
        tr = data.get("translate_result")
        if tr is None:
            msg = "finish event missing translate_result"
            raise ValueError(msg)
        result_model = translation_result_from_runtime(tr)
        fin = TranslationFinishedEvent(translation_result=result_model)
        return fin.model_dump(mode="json")
    if t == ProgressEventType.ERROR:
        raw_err = data.get("error", "")
        if isinstance(raw_err, TranslationErrorPayload):
            err_payload = raw_err
        elif isinstance(raw_err, dict):
            err_payload = TranslationErrorPayload.model_validate(raw_err)
        elif isinstance(raw_err, BaseException):
            err_payload = TranslationErrorPayload(
                code=PublicErrorCode.INTERNAL_ERROR,
                message=str(raw_err),
                details={"exception_type": type(raw_err).__name__},
            )
        elif isinstance(raw_err, type) and issubclass(raw_err, BaseException):
            canceled = raw_err.__name__ == "CancelledError"
            err_payload = TranslationErrorPayload(
                code=PublicErrorCode.CANCELED
                if canceled
                else PublicErrorCode.INTERNAL_ERROR,
                message=raw_err.__name__,
                details={"exception_type": "exception_class_ref"},
            )
        else:
            err_payload = TranslationErrorPayload(
                code=PublicErrorCode.INTERNAL_ERROR,
                message=str(raw_err),
                details={"exception_type": type(raw_err).__name__},
            )
        err_ev = TranslationErrorEvent(error=err_payload)
        return err_ev.model_dump(mode="json")
    msg = f"Unknown progress event type: {t!r}"
    raise ValueError(msg)


def _sha256_optional(path: Path | None) -> tuple[str | None, int | None]:
    if path is None or not path.is_file():
        return None, None
    h = hashlib.sha256()
    size = path.stat().st_size
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest(), size


def translation_result_from_runtime(translate_result: Any) -> TranslationResult:
    """Build :class:`TranslationResult` from runtime translate result (duck-typed)."""
    orig = str(getattr(translate_result, "original_pdf_path", "") or "")
    total_s = getattr(translate_result, "total_seconds", None)
    peak = getattr(translate_result, "peak_memory_usage", None)
    peak_mb = float(peak) if peak is not None else None

    items: list[ArtifactDescriptor] = []
    pairs: list[tuple[ArtifactKind, Any]] = [
        (
            ArtifactKind.MONO_PLAIN_PDF,
            getattr(translate_result, "mono_plain_pdf", None),
        ),
        (
            ArtifactKind.MONO_WATERMARKED_PDF,
            getattr(translate_result, "mono_watermarked_pdf", None),
        ),
        (
            ArtifactKind.DUAL_PLAIN_PDF,
            getattr(translate_result, "dual_plain_pdf", None),
        ),
        (
            ArtifactKind.DUAL_WATERMARKED_PDF,
            getattr(translate_result, "dual_watermarked_pdf", None),
        ),
        (
            ArtifactKind.AUTO_EXTRACTED_GLOSSARY_CSV,
            getattr(translate_result, "auto_extracted_glossary_path", None),
        ),
    ]
    for kind, p in pairs:
        if p is None:
            continue
        path = Path(p) if not isinstance(p, Path) else p
        digest, size = _sha256_optional(path)
        mt = (
            "text/csv"
            if kind == ArtifactKind.AUTO_EXTRACTED_GLOSSARY_CSV
            else "application/pdf"
        )
        items.append(
            ArtifactDescriptor(
                kind=kind,
                path=str(path.resolve()),
                sha256=digest,
                size_bytes=size,
                media_type=mt,
            )
        )

    summary = TranslationSummary(
        original_pdf_path=orig,
        total_seconds=float(total_s) if total_s is not None else None,
        peak_memory_usage_mb=peak_mb,
        total_valid_character_count=getattr(
            translate_result,
            "total_valid_character_count",
            None,
        ),
        total_valid_text_token_count=getattr(
            translate_result,
            "total_valid_text_token_count",
            None,
        ),
    )
    return TranslationResult(summary=summary, artifacts=ArtifactManifest(items=items))
