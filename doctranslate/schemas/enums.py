"""Stable enums for the public engine API (wire-format safe values)."""

from __future__ import annotations

from enum import Enum


class PublicErrorCode(str, Enum):
    """Machine-readable error codes for public API and JSON CLI."""

    VALIDATION_ERROR = "validation_error"
    INPUT_ERROR = "input_error"
    TRANSLATOR_ERROR = "translator_error"
    INTERNAL_ERROR = "internal_error"
    CANCELED = "canceled"
    UNSUPPORTED_CONFIGURATION = "unsupported_configuration"
    NOT_FOUND = "not_found"
    OPEN_FAILED = "open_failed"


class ArtifactKind(str, Enum):
    """Kinds of outputs produced by a translation job."""

    MONO_PLAIN_PDF = "mono_plain_pdf"
    MONO_WATERMARKED_PDF = "mono_watermarked_pdf"
    DUAL_PLAIN_PDF = "dual_plain_pdf"
    DUAL_WATERMARKED_PDF = "dual_watermarked_pdf"
    AUTO_EXTRACTED_GLOSSARY_CSV = "auto_extracted_glossary_csv"
    METRICS_JSON = "metrics_json"


class ProgressEventType(str, Enum):
    """Discriminator values for progress stream events."""

    STAGE_SUMMARY = "stage_summary"
    PROGRESS_START = "progress_start"
    PROGRESS_UPDATE = "progress_update"
    PROGRESS_END = "progress_end"
    FINISH = "finish"
    ERROR = "error"


class TranslatorMode(str, Enum):
    """How translators are constructed for a job."""

    OPENAI = "openai"
    ROUTER = "router"
    LOCAL = "local"
