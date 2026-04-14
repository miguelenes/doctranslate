"""Normalized types for multi-provider translation (requests, capabilities, failures)."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any
from typing import Generic
from typing import TypeVar

from pydantic import BaseModel


class RouterStrategy(str, Enum):
    """Translation routing strategies."""

    FAILOVER = "failover"
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    COST_AWARE = "cost_aware"


class FailureCategory(str, Enum):
    """Normalized failure categories for routing and metrics."""

    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    SERVER_ERROR = "server_error"
    PARTIAL_OUTAGE = "partial_outage"
    AUTHENTICATION = "authentication"
    MALFORMED_RESPONSE = "malformed_response"
    CONTENT_FILTER = "content_filter"
    BAD_REQUEST = "bad_request"
    UNKNOWN = "unknown"


class LLMOutputMode(str, Enum):
    """How the model should format completion output."""

    TEXT = "text"
    JSON_OBJECT = "json_object"
    JSON_SCHEMA = "json_schema"


class LLMTransportKind(str, Enum):
    """Which HTTP/API surface was used for a completion."""

    OPENAI_RESPONSES = "openai_responses"
    OPENAI_CHAT_COMPLETIONS = "openai_chat_completions"
    LITELLM = "litellm"
    UNKNOWN = "unknown"


@dataclass
class TranslatorCapabilities:
    """Structured capability flags for pipeline routing (no ``do_llm_translate(None)`` probes)."""

    supports_llm: bool = False
    supports_json_mode: bool = False
    supports_reasoning: bool = False
    supports_streaming: bool = False
    supports_structured_outputs: bool = False
    supports_responses_api: bool | None = None
    max_output_tokens: int = 2048
    rpm: int | None = None
    tpm: int | None = None
    provider_id: str = ""


@dataclass
class TokenUsage:
    """Token usage from one completion."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cache_hit_prompt_tokens: int = 0


@dataclass
class ProviderUsage:
    """Usage and cost for observability."""

    provider_id: str
    latency_ms: float = 0.0
    tokens: TokenUsage = field(default_factory=TokenUsage)
    estimated_cost_usd: float = 0.0
    raw_response: Any = None


@dataclass
class CompletionResult:
    """Normalized LLM completion result."""

    text: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    estimated_cost_usd: float = 0.0
    latency_ms: float = 0.0
    raw_response: Any = None
    parsed: Any | None = None
    refusal: str | None = None
    transport: LLMTransportKind = LLMTransportKind.UNKNOWN


TSchema = TypeVar("TSchema")


@dataclass
class LLMRequestOptions:
    """Per-request generation and formatting options."""

    temperature: float | None = 0.0
    max_output_tokens: int | None = 2048
    reasoning_effort: str | None = None
    output_mode: LLMOutputMode = LLMOutputMode.TEXT
    schema_name: str | None = None
    structured_model: type[BaseModel] | None = None
    extra_headers: dict[str, str] = field(default_factory=dict)
    extra_body: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMRequest(Generic[TSchema]):
    """Typed LLM request (prompt construction stays outside the transport)."""

    operation: str
    prompt_version: str
    messages: list[dict[str, str]]
    options: LLMRequestOptions = field(default_factory=LLMRequestOptions)
    cache_fingerprint: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMCompletion(Generic[TSchema]):
    """Normalized completion including optional parsed structured output."""

    text: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    parsed: TSchema | None = None
    refusal: str | None = None
    estimated_cost_usd: float = 0.0
    latency_ms: float = 0.0
    raw_response: Any = None
    transport: LLMTransportKind = LLMTransportKind.UNKNOWN


@dataclass
class NormalizedLLMError:
    """Structured error for logging and routing (no raw prompts)."""

    category: FailureCategory
    message: str
    provider_hint: str = ""
