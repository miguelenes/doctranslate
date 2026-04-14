"""Normalize token usage from OpenAI chat completions and Responses API."""

from __future__ import annotations

from typing import Any

from doctranslate.translator.types import TokenUsage


def token_usage_from_chat_completion(response: Any) -> TokenUsage:
    """Extract TokenUsage from a chat completion response object."""
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
    details = getattr(response, "prompt_tokens_details", None)
    if details is not None and getattr(details, "cached_tokens", 0):
        hit += int(getattr(details, "cached_tokens", 0) or 0)
    return TokenUsage(
        prompt_tokens=pt,
        completion_tokens=ct,
        total_tokens=tt,
        cache_hit_prompt_tokens=hit,
    )


def token_usage_from_openai_response(response: Any) -> TokenUsage:
    """Extract TokenUsage from ``responses.create`` response."""
    usage = getattr(response, "usage", None)
    if not usage:
        return TokenUsage()
    pt = int(
        getattr(usage, "input_tokens", None)
        or getattr(usage, "prompt_tokens", None)
        or 0,
    )
    ct = int(
        getattr(usage, "output_tokens", None)
        or getattr(usage, "completion_tokens", None)
        or 0,
    )
    tt = int(getattr(usage, "total_tokens", None) or 0)
    if not tt and (pt or ct):
        tt = pt + ct
    hit = 0
    details = getattr(usage, "input_tokens_details", None)
    if details is not None:
        hit = int(getattr(details, "cached_tokens", 0) or 0)
    return TokenUsage(
        prompt_tokens=pt,
        completion_tokens=ct,
        total_tokens=tt,
        cache_hit_prompt_tokens=hit,
    )
