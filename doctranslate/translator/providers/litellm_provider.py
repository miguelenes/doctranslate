"""LiteLLM-backed chat completion execution and error classification."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from doctranslate.translator.config import ProviderConfigModel, resolve_provider_api_key
from doctranslate.translator.types import CompletionResult, FailureCategory, TokenUsage

logger = logging.getLogger(__name__)


def build_litellm_model_id(cfg: ProviderConfigModel) -> str:
    """Return LiteLLM model string for ``litellm.completion``."""
    p = cfg.provider
    m = cfg.model.strip()
    if p == "openai":
        return m if m.startswith("openai/") else f"openai/{m}"
    if p == "anthropic":
        return m if m.startswith("anthropic/") else f"anthropic/{m}"
    if p == "openrouter":
        return m if m.startswith("openrouter/") else f"openrouter/{m}"
    if p == "ollama":
        return m if m.startswith("ollama/") else f"ollama/{m}"
    if p == "openai_compatible":
        return m if m.startswith("openai/") else f"openai/{m}"
    msg = f"Unknown provider: {p}"
    raise ValueError(msg)


def classify_exception(exc: BaseException) -> FailureCategory:
    """Map SDK/LiteLLM/HTTP errors to normalized failure categories."""
    if isinstance(exc, MalformedLLMResponseError):
        return FailureCategory.MALFORMED_RESPONSE
    try:
        import openai

        if isinstance(exc, openai.AuthenticationError):
            return FailureCategory.AUTHENTICATION
        if isinstance(exc, openai.RateLimitError):
            return FailureCategory.RATE_LIMIT
        if isinstance(exc, openai.APITimeoutError):
            return FailureCategory.TIMEOUT
        if isinstance(exc, openai.BadRequestError):
            return FailureCategory.BAD_REQUEST
        if isinstance(exc, openai.APIStatusError):
            code = getattr(exc, "status_code", None) or 0
            if code in (502, 503, 504):
                return FailureCategory.PARTIAL_OUTAGE
            if code >= 500:
                return FailureCategory.SERVER_ERROR
            return FailureCategory.BAD_REQUEST
        if isinstance(exc, openai.APIConnectionError):
            return FailureCategory.PARTIAL_OUTAGE
    except ImportError:
        pass

    if isinstance(exc, httpx.TimeoutException):
        return FailureCategory.TIMEOUT
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code if exc.response is not None else 0
        if code == 429:
            return FailureCategory.RATE_LIMIT
        if code in (401, 403):
            return FailureCategory.AUTHENTICATION
        if code in (502, 503, 504):
            return FailureCategory.PARTIAL_OUTAGE
        if code >= 500:
            return FailureCategory.SERVER_ERROR
        return FailureCategory.BAD_REQUEST

    name = type(exc).__name__.lower()
    msg = str(exc).lower()
    if "rate" in name or "429" in msg or "rate limit" in msg:
        return FailureCategory.RATE_LIMIT
    if "timeout" in name or "timed out" in msg:
        return FailureCategory.TIMEOUT
    if "auth" in name or "401" in msg or "403" in msg:
        return FailureCategory.AUTHENTICATION
    if "content" in msg and ("policy" in msg or "filter" in msg or "moderation" in msg):
        return FailureCategory.CONTENT_FILTER
    return FailureCategory.UNKNOWN


def _usage_from_response(response: Any) -> TokenUsage:
    usage = getattr(response, "usage", None)
    if not usage:
        return TokenUsage()
    pt = int(getattr(usage, "prompt_tokens", None) or 0)
    ct = int(getattr(usage, "completion_tokens", None) or 0)
    tt = int(getattr(usage, "total_tokens", None) or 0)
    if not tt and (pt or ct):
        tt = pt + ct
    hit = 0
    if hasattr(usage, "prompt_cache_hit_tokens"):
        hit = int(getattr(usage, "prompt_cache_hit_tokens", 0) or 0)
    return TokenUsage(
        prompt_tokens=pt,
        completion_tokens=ct,
        total_tokens=tt,
        cache_hit_prompt_tokens=hit,
    )


def estimate_cost_usd(
    usage: TokenUsage,
    in_per_mtok: float | None,
    out_per_mtok: float | None,
) -> float:
    if in_per_mtok is None and out_per_mtok is None:
        return 0.0
    ip = (usage.prompt_tokens / 1_000_000.0) * (in_per_mtok or 0.0)
    op = (usage.completion_tokens / 1_000_000.0) * (out_per_mtok or 0.0)
    return ip + op


class LiteLLMProviderExecutor:
    """Execute one chat completion for a resolved provider config."""

    def __init__(self, provider_id: str, cfg: ProviderConfigModel):
        self.provider_id = provider_id
        self.cfg = cfg
        self.litellm_model = build_litellm_model_id(cfg)

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        json_mode: bool = False,
    ) -> CompletionResult:
        import litellm

        api_key = resolve_provider_api_key(self.cfg)
        kwargs: dict[str, Any] = {
            "model": self.litellm_model,
            "messages": messages,
            "timeout": self.cfg.timeout_seconds,
            "num_retries": 0,
        }
        if api_key:
            kwargs["api_key"] = api_key
        if self.cfg.base_url:
            kwargs["api_base"] = self.cfg.base_url
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        kwargs["max_tokens"] = self.cfg.max_output_tokens

        t0 = time.perf_counter()
        try:
            response = litellm.completion(**kwargs)
        except Exception:
            raise
        latency_ms = (time.perf_counter() - t0) * 1000.0

        usage = _usage_from_response(response)
        cost = estimate_cost_usd(
            usage,
            self.cfg.input_cost_per_million_tokens,
            self.cfg.output_cost_per_million_tokens,
        )

        try:
            choice0 = response.choices[0]
            msg = choice0.message
            content = (msg.content or "").strip() if msg is not None else ""
        except (IndexError, AttributeError) as e:
            raise MalformedLLMResponseError("Missing choices/message in response") from e

        if not content:
            raise MalformedLLMResponseError("Empty model content")

        return CompletionResult(
            text=content,
            usage=usage,
            estimated_cost_usd=cost,
            latency_ms=latency_ms,
            raw_response=response,
        )


class MalformedLLMResponseError(RuntimeError):
    """Raised when the response shape is unusable."""

    pass
