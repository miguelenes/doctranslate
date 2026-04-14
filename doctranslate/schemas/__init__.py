"""Typed configuration models with minimal third-party imports (schemas profile).

Prefer importing from this package for config validation in external apps.
Heavy PDF, LLM, and OCR stacks are *not* imported here.

Public engine contracts (:class:`TranslationRequest`, progress events, etc.) live
in :mod:`doctranslate.schemas.public_api` and are re-exported from this package.
"""

from __future__ import annotations

from doctranslate.format.pdf.translation_settings import TranslationSettings
from doctranslate.format.pdf.translation_settings import WatermarkOutputMode
from doctranslate.schemas.enums import ArtifactKind
from doctranslate.schemas.enums import ProgressEventType
from doctranslate.schemas.enums import PublicErrorCode
from doctranslate.schemas.enums import TranslatorMode
from doctranslate.schemas.public_api import ArtifactDescriptor
from doctranslate.schemas.public_api import ArtifactManifest
from doctranslate.schemas.public_api import CliJsonEnvelope
from doctranslate.schemas.public_api import CliProgressLine
from doctranslate.schemas.public_api import GlossaryEntrySpec
from doctranslate.schemas.public_api import GlossarySpec
from doctranslate.schemas.public_api import InputFileInspection
from doctranslate.schemas.public_api import InputInspectionResult
from doctranslate.schemas.public_api import OpenAIRequestArgs
from doctranslate.schemas.public_api import TranslationErrorPayload
from doctranslate.schemas.public_api import TranslationMemorySpec
from doctranslate.schemas.public_api import TranslationOptions
from doctranslate.schemas.public_api import TranslationRequest
from doctranslate.schemas.public_api import TranslationResult
from doctranslate.schemas.public_api import TranslationSummary
from doctranslate.schemas.public_api import TranslatorRequestConfig
from doctranslate.schemas.public_api import progress_event_from_dict
from doctranslate.schemas.public_api import translation_result_from_runtime
from doctranslate.schemas.versions import PROGRESS_EVENT_VERSION
from doctranslate.schemas.versions import PUBLIC_SCHEMA_VERSION
from doctranslate.translator.config import NestedTranslatorConfig
from doctranslate.translator.config import ProviderConfigModel
from doctranslate.translator.config import RouteProfileConfig
from doctranslate.translator.config import load_nested_translator_config
from doctranslate.translator.config import merge_cli_router_overrides_from_mapping
from doctranslate.translator.config import resolve_provider_api_key
from doctranslate.translator.config import validate_router_config
from doctranslate.translator.types import FailureCategory
from doctranslate.translator.types import LLMOutputMode
from doctranslate.translator.types import LLMTransportKind
from doctranslate.translator.types import RouterStrategy
from doctranslate.translator.types import TokenUsage
from doctranslate.translator.types import TranslatorCapabilities

__all__ = [
    "ArtifactDescriptor",
    "ArtifactKind",
    "ArtifactManifest",
    "CliJsonEnvelope",
    "CliProgressLine",
    "FailureCategory",
    "GlossaryEntrySpec",
    "GlossarySpec",
    "InputFileInspection",
    "InputInspectionResult",
    "LLMOutputMode",
    "LLMTransportKind",
    "NestedTranslatorConfig",
    "OpenAIRequestArgs",
    "PROGRESS_EVENT_VERSION",
    "PUBLIC_SCHEMA_VERSION",
    "ProgressEventType",
    "ProviderConfigModel",
    "PublicErrorCode",
    "RouteProfileConfig",
    "RouterStrategy",
    "TokenUsage",
    "TranslatorCapabilities",
    "TranslatorMode",
    "TranslatorRequestConfig",
    "TranslationErrorPayload",
    "TranslationMemorySpec",
    "TranslationOptions",
    "TranslationRequest",
    "TranslationResult",
    "TranslationSettings",
    "TranslationSummary",
    "WatermarkOutputMode",
    "load_nested_translator_config",
    "merge_cli_router_overrides_from_mapping",
    "progress_event_from_dict",
    "resolve_provider_api_key",
    "translation_result_from_runtime",
    "validate_router_config",
]
