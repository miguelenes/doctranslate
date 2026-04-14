"""Normalized types for multi-provider translation (requests, capabilities, failures)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


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


@dataclass
class TranslatorCapabilities:
    """Structured capability flags for pipeline routing (no ``do_llm_translate(None)`` probes)."""

    supports_llm: bool = False
    supports_json_mode: bool = False
    supports_reasoning: bool = False
    supports_streaming: bool = False
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
