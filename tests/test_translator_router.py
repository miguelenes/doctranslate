"""Tests for sync ``TranslatorRouter``."""

from unittest.mock import MagicMock

import pytest

from doctranslate.translator.config import NestedTranslatorConfig, ProviderConfigModel
from doctranslate.translator.config import RouteProfileConfig
from doctranslate.translator.router import TranslatorRouter
from doctranslate.translator.translator import TranslationError
from doctranslate.translator.types import CompletionResult, RouterStrategy, TokenUsage
from doctranslate.translator.types import TranslatorCapabilities


def _router(
    *,
    strategy: RouterStrategy = RouterStrategy.FAILOVER,
    side_effects: tuple | None = None,
):
    p1 = ProviderConfigModel(provider="openai", model="gpt-4o-mini", api_key="k1")
    p2 = ProviderConfigModel(provider="openai", model="gpt-4o-mini", api_key="k2")
    cfgs = {"a": p1, "b": p2}
    caps = {
        "a": TranslatorCapabilities(
            supports_llm=True,
            supports_json_mode=True,
            provider_id="a",
        ),
        "b": TranslatorCapabilities(
            supports_llm=True,
            supports_json_mode=True,
            provider_id="b",
        ),
    }
    ex_a = MagicMock()
    ex_b = MagicMock()
    if side_effects is None:
        ok = CompletionResult(
            text="done",
            usage=TokenUsage(
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
                cache_hit_prompt_tokens=0,
            ),
            estimated_cost_usd=0.0,
            latency_ms=1.0,
        )
        ex_a.complete.return_value = ok
        ex_b.complete.return_value = ok
    else:
        a0, b0 = side_effects
        if isinstance(a0, BaseException):
            ex_a.complete.side_effect = a0
        else:
            ex_a.complete.return_value = a0
        if isinstance(b0, BaseException):
            ex_b.complete.side_effect = b0
        else:
            ex_b.complete.return_value = b0

    profile = RouteProfileConfig(
        providers=["a", "b"],
        strategy=strategy,
        max_attempts=4,
    )
    nested = NestedTranslatorConfig()
    return TranslatorRouter(
        lang_in="en",
        lang_out="zh",
        ignore_cache=True,
        profile_name="translate",
        route_profile=profile,
        global_strategy=strategy,
        executors={"a": ex_a, "b": ex_b},
        capabilities_by_id=caps,
        provider_configs=cfgs,
        nested_settings=nested,
    )


def test_failover_uses_second_on_first_failure():
    r = _router(
        strategy=RouterStrategy.FAILOVER,
        side_effects=(
            RuntimeError("rate limited"),
            CompletionResult(
                text="ok",
                usage=TokenUsage(
                    prompt_tokens=1,
                    completion_tokens=1,
                    total_tokens=2,
                    cache_hit_prompt_tokens=0,
                ),
                estimated_cost_usd=0.0,
                latency_ms=1.0,
            ),
        ),
    )
    out = r.do_llm_translate("hello", rate_limit_params={})
    assert out == "ok"


def test_all_fail_raises_translation_error():
    r = _router(
        side_effects=(
            RuntimeError("e1"),
            RuntimeError("e2"),
        ),
    )
    with pytest.raises(TranslationError):
        r.do_llm_translate("x", rate_limit_params={})
