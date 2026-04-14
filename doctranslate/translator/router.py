"""
Multi-Translator Orchestration Engine

This module provides advanced routing and fallback capabilities across multiple
translation backends (OpenAI, Anthropic, local Ollama, etc.). It allows:

- Automatic failover when primary translator hits rate limits or errors
- Per-backend cost tracking and quota management
- Quality scoring via back-translation similarity (optional)
- Balanced load distribution across available translators

Architecture:
    TranslatorRouter: Main router that implements BaseTranslator interface
    ├── Multiple backend instances (OpenAITranslator, AnthropicTranslator, etc.)
    ├── Router strategy (round-robin, least-loaded, quality-based)
    └── Per-backend metrics (cost, latency, error rate)

Usage Example:
    router = TranslatorRouter([
        OpenAITranslator(model="gpt-4", api_key=...),
        AnthropicTranslator(model="claude-3-opus", api_key=...),
    ])
    router.set_strategy("failover")  # Use first available, fallback on error
    translated = await router.translate("Hello", "en", "zh")
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .translator import BaseTranslator, TranslationError

logger = logging.getLogger(__name__)


class RouterStrategy(str, Enum):
    """Translation routing strategies."""

    FAILOVER = "failover"  # Use first available, fallback on error
    ROUND_ROBIN = "round_robin"  # Cycle through translators
    LEAST_LOADED = "least_loaded"  # Pick translator with lowest concurrent load
    COST_AWARE = "cost_aware"  # Pick cheapest option that meets quality threshold


@dataclass
class TranslatorMetrics:
    """Per-translator metrics for monitoring and decision-making."""

    name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_cost: float = 0.0
    total_tokens: int = 0
    avg_latency_ms: float = 0.0
    concurrent_requests: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    error_rate_window: Dict[str, int] = field(default_factory=dict)  # Rolling window of errors

    @property
    def success_rate(self) -> float:
        """Return success rate as percentage (0-100)."""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def cost_per_token(self) -> float:
        """Return average cost per token."""
        if self.total_tokens == 0:
            return 0.0
        return self.total_cost / self.total_tokens

    @property
    def is_healthy(self) -> bool:
        """Check if translator is in good health (success rate > 80%)."""
        return self.success_rate >= 80.0


class QualityScorer(ABC):
    """Abstract base for translation quality scoring."""

    @abstractmethod
    async def score(self, original: str, translation: str, target_lang: str) -> float:
        """
        Score translation quality (0.0 to 1.0).

        Args:
            original: Original text
            translation: Translated text
            target_lang: Target language code

        Returns:
            Quality score between 0.0 (poor) and 1.0 (excellent)
        """
        pass


class SimpleBackTranslationScorer(QualityScorer):
    """
    Score translations by back-translating and comparing similarity to original.

    This is a simple implementation. In production, consider using:
    - BLEU score for statistical similarity
    - Semantic similarity (embeddings-based)
    - Native speaker ratings
    """

    def __init__(self, scorer_translator: BaseTranslator):
        """
        Initialize with a translator to perform back-translation.

        Args:
            scorer_translator: A translator instance for back-translation
        """
        self.scorer_translator = scorer_translator

    async def score(self, original: str, translation: str, target_lang: str) -> float:
        """
        Score by back-translating from target_lang back to original language.

        Simple approach: calculate character overlap ratio.
        """
        try:
            # Back-translate: target_lang → original language (assume "en")
            back_translated = await self.scorer_translator.translate(
                translation,
                target_lang,
                "en",  # Assume original is English; make this configurable in production
            )

            # Simple similarity: normalized character overlap
            original_chars = set(original.lower().replace(" ", ""))
            back_chars = set(back_translated.lower().replace(" ", ""))

            if not original_chars:
                return 1.0

            overlap = len(original_chars & back_chars)
            similarity = overlap / len(original_chars)

            # Clamp to [0, 1] and apply quality thresholds
            return min(1.0, max(0.0, similarity))

        except Exception as e:
            logger.warning(f"Back-translation scoring failed: {e}")
            return 0.5  # Neutral score if scoring fails


class TranslatorRouter(BaseTranslator):
    """
    Multi-translator router with failover, load balancing, and cost awareness.

    This router implements the BaseTranslator interface, so it can be used
    as a drop-in replacement for single-translator setups.
    """

    def __init__(
        self,
        translators: List[BaseTranslator],
        strategy: RouterStrategy = RouterStrategy.FAILOVER,
        quality_scorer: Optional[QualityScorer] = None,
    ):
        """
        Initialize router with multiple translators.

        Args:
            translators: List of BaseTranslator instances to route between
            strategy: Routing strategy to use
            quality_scorer: Optional QualityScorer for quality-based routing
        """
        if not translators:
            raise ValueError("At least one translator is required")

        self.translators = translators
        self.strategy = strategy
        self.quality_scorer = quality_scorer
        self._current_index = 0  # For round-robin
        self.metrics: Dict[str, TranslatorMetrics] = {
            t.__class__.__name__: TranslatorMetrics(name=t.__class__.__name__) for t in translators
        }

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        **kwargs,
    ) -> str:
        """
        Translate text using the selected routing strategy.

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            **kwargs: Additional arguments passed to translator

        Returns:
            Translated text

        Raises:
            TranslationError: If all translators fail
        """
        if self.strategy == RouterStrategy.FAILOVER:
            return await self._translate_failover(text, source_lang, target_lang, **kwargs)
        elif self.strategy == RouterStrategy.ROUND_ROBIN:
            return await self._translate_round_robin(text, source_lang, target_lang, **kwargs)
        elif self.strategy == RouterStrategy.LEAST_LOADED:
            return await self._translate_least_loaded(text, source_lang, target_lang, **kwargs)
        elif self.strategy == RouterStrategy.COST_AWARE:
            return await self._translate_cost_aware(text, source_lang, target_lang, **kwargs)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

    async def _translate_failover(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        **kwargs,
    ) -> str:
        """Try each translator in order until one succeeds."""
        last_error = None

        for translator in self.translators:
            translator_name = translator.__class__.__name__
            metrics = self.metrics[translator_name]

            try:
                metrics.concurrent_requests += 1
                result = await translator.translate(text, source_lang, target_lang, **kwargs)

                metrics.successful_requests += 1
                metrics.total_requests += 1
                metrics.concurrent_requests -= 1

                logger.info(f"Translation succeeded with {translator_name}")
                return result

            except Exception as e:
                metrics.failed_requests += 1
                metrics.total_requests += 1
                metrics.last_error = str(e)
                metrics.last_error_time = datetime.now()
                metrics.concurrent_requests -= 1

                last_error = e
                logger.warning(f"Translation failed with {translator_name}: {e}. Trying next...")

        # All translators failed
        raise TranslationError(f"All translators failed. Last error: {last_error}")

    async def _translate_round_robin(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        **kwargs,
    ) -> str:
        """Cycle through translators in round-robin fashion."""
        for attempt in range(len(self.translators)):
            translator = self.translators[self._current_index % len(self.translators)]
            self._current_index += 1
            translator_name = translator.__class__.__name__
            metrics = self.metrics[translator_name]

            try:
                metrics.concurrent_requests += 1
                result = await translator.translate(text, source_lang, target_lang, **kwargs)

                metrics.successful_requests += 1
                metrics.total_requests += 1
                metrics.concurrent_requests -= 1

                return result

            except Exception as e:
                metrics.failed_requests += 1
                metrics.total_requests += 1
                metrics.concurrent_requests -= 1

                if attempt == len(self.translators) - 1:
                    raise TranslationError(f"All translators failed in round-robin. Last error: {e}")

        raise TranslationError("Round-robin failed")

    async def _translate_least_loaded(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        **kwargs,
    ) -> str:
        """Pick translator with fewest concurrent requests."""
        translator = min(
            self.translators,
            key=lambda t: self.metrics[t.__class__.__name__].concurrent_requests,
        )
        translator_name = translator.__class__.__name__
        metrics = self.metrics[translator_name]

        try:
            metrics.concurrent_requests += 1
            result = await translator.translate(text, source_lang, target_lang, **kwargs)

            metrics.successful_requests += 1
            metrics.total_requests += 1
            metrics.concurrent_requests -= 1

            return result

        except Exception as e:
            metrics.failed_requests += 1
            metrics.total_requests += 1
            metrics.concurrent_requests -= 1

            # Fallback to failover on least-loaded failure
            logger.warning(f"Least-loaded translator failed, falling back to failover: {e}")
            return await self._translate_failover(text, source_lang, target_lang, **kwargs)

    async def _translate_cost_aware(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        **kwargs,
    ) -> str:
        """Select cheapest healthy translator (success rate > 80%)."""
        healthy_translators = [
            t for t in self.translators if self.metrics[t.__class__.__name__].is_healthy
        ]

        if not healthy_translators:
            # Fall back to all translators if none are healthy
            healthy_translators = self.translators

        # Sort by cost per token
        sorted_translators = sorted(
            healthy_translators,
            key=lambda t: self.metrics[t.__class__.__name__].cost_per_token,
        )

        for translator in sorted_translators:
            translator_name = translator.__class__.__name__
            metrics = self.metrics[translator_name]

            try:
                metrics.concurrent_requests += 1
                result = await translator.translate(text, source_lang, target_lang, **kwargs)

                metrics.successful_requests += 1
                metrics.total_requests += 1
                metrics.concurrent_requests -= 1

                return result

            except Exception as e:
                metrics.failed_requests += 1
                metrics.total_requests += 1
                metrics.concurrent_requests -= 1

                logger.warning(f"Cost-aware selection failed with {translator_name}: {e}")

        raise TranslationError("Cost-aware routing: all translators failed")

    def set_strategy(self, strategy: RouterStrategy) -> None:
        """Change routing strategy at runtime."""
        self.strategy = strategy
        logger.info(f"Router strategy changed to: {strategy.value}")

    def get_metrics(self) -> Dict[str, TranslatorMetrics]:
        """Return current metrics for all translators."""
        return dict(self.metrics)

    def print_metrics(self) -> str:
        """Return formatted metrics string for logging."""
        lines = ["TranslatorRouter Metrics:", "-" * 70]

        for name, metrics in self.metrics.items():
            lines.append(f"{name}:")
            lines.append(f"  Requests: {metrics.total_requests} (✓ {metrics.successful_requests}, ✗ {metrics.failed_requests})")
            lines.append(f"  Success Rate: {metrics.success_rate:.1f}%")
            lines.append(f"  Avg Latency: {metrics.avg_latency_ms:.2f}ms")
            lines.append(f"  Total Cost: ${metrics.total_cost:.4f}")
            lines.append(f"  Cost/Token: ${metrics.cost_per_token:.6f}")
            if metrics.last_error:
                lines.append(f"  Last Error: {metrics.last_error} ({metrics.last_error_time})")

        return "\n".join(lines)
