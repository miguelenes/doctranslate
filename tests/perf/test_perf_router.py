"""Micro-benchmarks for ``TranslatorRouter`` (mocked providers, no network)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from doctranslate.translator.config import NestedTranslatorConfig
from doctranslate.translator.config import ProviderConfigModel
from doctranslate.translator.config import RouteProfileConfig
from doctranslate.translator.router import TranslatorRouter
from doctranslate.translator.types import CompletionResult
from doctranslate.translator.types import RouterStrategy
from doctranslate.translator.types import TokenUsage
from doctranslate.translator.types import TranslatorCapabilities


def _router_failover_ok():
    p1 = ProviderConfigModel(provider="openai", model="gpt-4o-mini", api_key="k1")
    cfgs = {"a": p1}
    caps = {
        "a": TranslatorCapabilities(
            supports_llm=True,
            supports_json_mode=True,
            provider_id="a",
        ),
    }
    ex_a = MagicMock()
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
    profile = RouteProfileConfig(
        providers=["a"],
        strategy=RouterStrategy.FAILOVER,
        max_attempts=4,
    )
    nested = NestedTranslatorConfig()
    return TranslatorRouter(
        lang_in="en",
        lang_out="zh",
        ignore_cache=True,
        profile_name="translate",
        route_profile=profile,
        global_strategy=RouterStrategy.FAILOVER,
        executors={"a": ex_a},
        capabilities_by_id=caps,
        provider_configs=cfgs,
        nested_settings=nested,
    )


@pytest.mark.perf
def test_perf_router_do_llm_translate(benchmark):
    """Single successful router completion (mocked LiteLLM executor)."""
    r = _router_failover_ok()

    def _call():
        return r.do_llm_translate("hello world", rate_limit_params={})

    out = benchmark(_call)
    assert out == "done"
