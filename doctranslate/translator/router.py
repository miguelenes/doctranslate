"""
Multi-provider translation router (sync, ``BaseTranslator``-compatible).

Uses LiteLLM for provider normalization; applies failover, round-robin,
least-loaded, and cost-aware strategies with health and cooldown tracking.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from doctranslate.babeldoc_exception.BabelDOCException import ContentFilterError
from doctranslate.translator.config import (
    NestedTranslatorConfig,
    ProviderConfigModel,
    RouteProfileConfig,
)
from doctranslate.translator.providers.litellm_provider import (
    LiteLLMProviderExecutor,
    MalformedLLMResponseError,
    classify_exception,
)
from doctranslate.translator.translator import BaseTranslator, TranslationError
from doctranslate.translator.types import (
    FailureCategory,
    RouterStrategy,
    TranslatorCapabilities,
)
from doctranslate.utils.atomic_integer import AtomicInteger

logger = logging.getLogger(__name__)

_COOLDOWN_RATE_LIMIT_S = 30.0
_COOLDOWN_AUTH_S = 86400.0 * 365


@dataclass
class ProviderMetrics:
    """Per-provider metrics for observability."""

    provider_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    failures_by_category: dict[str, int] = field(default_factory=dict)
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    concurrent_requests: int = 0
    last_error: str | None = None
    last_error_time: datetime | None = None

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100.0

    @property
    def avg_latency_ms(self) -> float:
        if self.successful_requests == 0:
            return 0.0
        return self.total_latency_ms / self.successful_requests

    @property
    def cost_per_token(self) -> float:
        if self.total_tokens == 0:
            return 0.0
        return self.total_cost_usd / self.total_tokens

    def health_score(self) -> float:
        return self.successful_requests / max(self.total_requests, 1)


class TranslatorRouter(BaseTranslator):
    """
    Sync router implementing ``do_translate`` / ``do_llm_translate`` for the PDF pipeline.
    """

    name = "router"

    def __init__(
        self,
        lang_in: str,
        lang_out: str,
        ignore_cache: bool,
        profile_name: str,
        route_profile: RouteProfileConfig,
        global_strategy: RouterStrategy,
        executors: dict[str, LiteLLMProviderExecutor],
        capabilities_by_id: dict[str, TranslatorCapabilities],
        provider_configs: dict[str, ProviderConfigModel],
        nested_settings: NestedTranslatorConfig,
    ):
        super().__init__(lang_in, lang_out, ignore_cache)
        self.model = profile_name
        self.profile_name = profile_name
        self.route_profile = route_profile
        self.strategy = global_strategy
        self._executors = executors
        self._capabilities = capabilities_by_id
        self._provider_cfgs = provider_configs
        self._nested = nested_settings
        self._metrics: dict[str, ProviderMetrics] = {
            pid: ProviderMetrics(provider_id=pid) for pid in route_profile.providers
        }
        self._cooldown_until: dict[str, float] = {}
        self._rr_lock = threading.Lock()
        self._rr_index = 0

        self.add_cache_impact_parameters("profile", profile_name)
        self.add_cache_impact_parameters("strategy", global_strategy.value)

        self.token_count = AtomicInteger()
        self.prompt_token_count = AtomicInteger()
        self.completion_token_count = AtomicInteger()
        self.cache_hit_prompt_token_count = AtomicInteger()

    @property
    def translator_capabilities(self) -> TranslatorCapabilities:
        """Union of capabilities across providers in this profile (conservative)."""
        ids = self.route_profile.providers
        if not ids:
            return TranslatorCapabilities(supports_llm=False, provider_id="router")
        caps = [self._capabilities[pid] for pid in ids if pid in self._capabilities]
        if not caps:
            return TranslatorCapabilities(supports_llm=True, provider_id="router")
        return TranslatorCapabilities(
            supports_llm=all(c.supports_llm for c in caps),
            supports_json_mode=all(c.supports_json_mode for c in caps),
            supports_reasoning=any(c.supports_reasoning for c in caps),
            supports_streaming=any(c.supports_streaming for c in caps),
            max_output_tokens=max(c.max_output_tokens for c in caps),
            provider_id=f"router:{self.profile_name}",
        )

    def _simple_messages(self, text: str) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": "You are a professional,authentic machine translation engine.",
            },
            {
                "role": "user",
                "content": (
                    f";; Treat next line as plain text input and translate it into {self.lang_out}, "
                    "output translation ONLY. If translation is unnecessary (e.g. proper nouns, codes, "
                    f"{{{{1}}}}, etc. ), return the original text. NO explanations. NO notes. Input:\n\n{text}"
                ),
            },
        ]

    def _in_cooldown(self, pid: str) -> bool:
        until = self._cooldown_until.get(pid)
        return until is not None and time.monotonic() < until

    def _set_cooldown(self, pid: str, category: FailureCategory) -> None:
        if category == FailureCategory.RATE_LIMIT:
            self._cooldown_until[pid] = time.monotonic() + _COOLDOWN_RATE_LIMIT_S
        elif category == FailureCategory.AUTHENTICATION:
            self._cooldown_until[pid] = time.monotonic() + _COOLDOWN_AUTH_S

    def _eligible_ids(self, require_json: bool, require_reasoning: bool) -> list[str]:
        out: list[str] = []
        for pid in self.route_profile.providers:
            if self._in_cooldown(pid):
                continue
            cap = self._capabilities.get(pid)
            if not cap:
                continue
            if require_json and not cap.supports_json_mode:
                continue
            if require_reasoning and not cap.supports_reasoning:
                continue
            if self.route_profile.min_health_score > 0:
                m = self._metrics.get(pid)
                if m and m.total_requests >= 3:
                    if m.health_score() < self.route_profile.min_health_score:
                        continue
            out.append(pid)
        return out

    def _order_provider_ids(self, candidates: list[str]) -> list[str]:
        if self.strategy == RouterStrategy.FAILOVER:
            return list(candidates)
        if self.strategy == RouterStrategy.ROUND_ROBIN:
            with self._rr_lock:
                n = len(candidates)
                if n == 0:
                    return []
                start = self._rr_index % n
                self._rr_index += 1
            return candidates[start:] + candidates[:start]
        if self.strategy == RouterStrategy.LEAST_LOADED:
            return sorted(
                candidates,
                key=lambda pid: self._metrics[pid].concurrent_requests,
            )
        if self.strategy == RouterStrategy.COST_AWARE:
            healthy = [
                pid
                for pid in candidates
                if self._metrics[pid].total_requests == 0
                or self._metrics[pid].health_score() >= 0.5
            ]
            pool = healthy or candidates

            def cost_key(pid: str) -> float:
                m = self._metrics[pid]
                cfg = self._provider_cfgs.get(pid)
                if m.total_tokens > 0 and m.total_cost_usd > 0:
                    return m.cost_per_token
                if cfg and cfg.input_cost_per_million_tokens is not None:
                    return cfg.input_cost_per_million_tokens / 1_000_000.0
                return 1e9

            return sorted(pool, key=cost_key)
        return list(candidates)

    def _record_success(self, pid: str, latency_ms: float, usage: Any, cost: float) -> None:
        m = self._metrics[pid]
        m.total_requests += 1
        m.successful_requests += 1
        m.concurrent_requests = max(0, m.concurrent_requests - 1)
        m.total_latency_ms += latency_ms
        m.total_cost_usd += cost
        m.total_tokens += int(usage.total_tokens or 0)
        self.token_count.inc(int(usage.total_tokens or 0))
        self.prompt_token_count.inc(int(usage.prompt_tokens or 0))
        self.completion_token_count.inc(int(usage.completion_tokens or 0))
        self.cache_hit_prompt_token_count.inc(int(usage.cache_hit_prompt_tokens or 0))

    def _record_failure_only(self, pid: str, exc: BaseException) -> FailureCategory:
        cat = classify_exception(exc)
        m = self._metrics[pid]
        m.total_requests += 1
        m.failed_requests += 1
        m.concurrent_requests = max(0, m.concurrent_requests - 1)
        m.failures_by_category[cat.value] = m.failures_by_category.get(cat.value, 0) + 1
        m.last_error = str(exc)
        m.last_error_time = datetime.now()
        self._set_cooldown(pid, cat)
        return cat

    def _route(
        self,
        *,
        messages: list[dict[str, str]],
        json_mode: bool,
    ) -> str:
        rp = self.route_profile
        require_json = json_mode or rp.require_json_mode
        require_reasoning = rp.require_reasoning
        candidates = self._eligible_ids(require_json, require_reasoning)
        ordered = self._order_provider_ids(candidates)
        if not ordered:
            ordered = self._order_provider_ids(
                [p for p in rp.providers if p in self._executors],
            )

        last_exc: BaseException | None = None
        attempts = 0
        max_attempts = max(1, rp.max_attempts)

        for pid in ordered:
            if attempts >= max_attempts:
                break
            if pid not in self._executors:
                continue
            m = self._metrics.setdefault(pid, ProviderMetrics(provider_id=pid))
            m.concurrent_requests += 1
            try:
                ex = self._executors[pid]
                result = ex.complete(messages, json_mode=json_mode)
                self._record_success(pid, result.latency_ms, result.usage, result.estimated_cost_usd)
                logger.info("Translation OK provider=%s profile=%s", pid, self.profile_name)
                return result.text
            except ContentFilterError:
                m.concurrent_requests = max(0, m.concurrent_requests - 1)
                raise
            except MalformedLLMResponseError as e:
                self._record_failure_only(pid, e)
                last_exc = e
                attempts += 1
                if FailureCategory.MALFORMED_RESPONSE not in rp.fallback_on:
                    raise
                logger.warning("Malformed response from %s: %s", pid, e)
            except Exception as e:
                cat = self._record_failure_only(pid, e)
                last_exc = e
                attempts += 1
                if cat == FailureCategory.CONTENT_FILTER and not rp.allow_content_filter_fallback:
                    raise
                if cat not in rp.fallback_on:
                    logger.warning(
                        "Provider %s error not in fallback_on (%s), stopping: %s",
                        pid,
                        cat,
                        e,
                    )
                    raise TranslationError(f"Routing failed on {pid}: {e}") from e
                logger.warning("Provider %s failed (%s): %s", pid, cat, e)

        raise TranslationError(f"All providers failed for profile={self.profile_name}: {last_exc}")

    def do_translate(self, text, rate_limit_params: dict = None):
        return self._route(messages=self._simple_messages(text), json_mode=False)

    def do_llm_translate(self, text, rate_limit_params: dict = None):
        if text is None:
            return None
        rlp = rate_limit_params or {}
        json_mode = bool(rlp.get("request_json_mode", False))
        messages = [{"role": "user", "content": text}]
        return self._route(messages=messages, json_mode=json_mode)

    def set_strategy(self, strategy: RouterStrategy) -> None:
        self.strategy = strategy
        logger.info("Router strategy changed to: %s", strategy.value)

    def get_metrics(self) -> dict[str, ProviderMetrics]:
        return dict(self._metrics)

    def get_metrics_summary_dict(self) -> dict[str, Any]:
        """Structured metrics for optional JSON export."""
        out: dict[str, Any] = {"profile": self.profile_name, "providers": {}}
        for pid, m in self._metrics.items():
            out["providers"][pid] = {
                "total_requests": m.total_requests,
                "successful_requests": m.successful_requests,
                "failed_requests": m.failed_requests,
                "failures_by_category": dict(m.failures_by_category),
                "total_cost_usd": round(m.total_cost_usd, 6),
                "total_tokens": m.total_tokens,
                "avg_latency_ms": round(m.avg_latency_ms, 2),
                "success_rate_pct": round(m.success_rate, 2),
            }
        return out

    def print_metrics(self) -> str:
        lines = ["TranslatorRouter Metrics:", "-" * 70, f"Profile: {self.profile_name}"]
        for pid, m in self._metrics.items():
            lines.append(f"{pid}:")
            lines.append(
                f"  Requests: {m.total_requests} (OK {m.successful_requests}, FAIL {m.failed_requests})",
            )
            lines.append(f"  Success rate: {m.success_rate:.1f}%")
            lines.append(f"  Avg latency: {m.avg_latency_ms:.2f}ms")
            lines.append(f"  Total cost USD: ${m.total_cost_usd:.4f}")
            lines.append(f"  Cost/token: ${m.cost_per_token:.8f}")
            if m.last_error:
                lines.append(f"  Last error: {m.last_error}")
        return "\n".join(lines)

    def flush_metrics_json(self, path: str | None) -> None:
        """Write metrics JSON if configured."""
        if not path or self._nested.metrics_output not in ("json", "both"):
            return
        payload = self.get_metrics_summary_dict()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
