"""Nested TOML configuration for multi-provider routing (Pydantic models)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import toml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from doctranslate.translator.types import FailureCategory, RouterStrategy


class RouteProfileConfig(BaseModel):
    """One named routing profile (e.g. paragraph translation vs term extraction)."""

    model_config = ConfigDict(extra="ignore")

    providers: list[str] = Field(default_factory=list)
    strategy: RouterStrategy = RouterStrategy.FAILOVER
    fallback_on: list[FailureCategory] = Field(
        default_factory=lambda: [
            FailureCategory.RATE_LIMIT,
            FailureCategory.TIMEOUT,
            FailureCategory.SERVER_ERROR,
            FailureCategory.MALFORMED_RESPONSE,
            FailureCategory.PARTIAL_OUTAGE,
            FailureCategory.UNKNOWN,
        ],
    )
    max_attempts: int = 4
    require_json_mode: bool = False
    require_reasoning: bool = False
    min_health_score: float = 0.0
    allow_content_filter_fallback: bool = False

    @field_validator("strategy", mode="before")
    @classmethod
    def _coerce_strategy(cls, v: Any) -> Any:
        if isinstance(v, RouterStrategy):
            return v
        if v is None:
            return RouterStrategy.FAILOVER
        return RouterStrategy(str(v))

    @field_validator("fallback_on", mode="before")
    @classmethod
    def _coerce_fallback_on(cls, v: Any) -> Any:
        if v is None:
            return v
        if not isinstance(v, list):
            return v
        out: list[FailureCategory] = []
        for item in v:
            if isinstance(item, FailureCategory):
                out.append(item)
            else:
                out.append(FailureCategory(str(item)))
        return out


class ProviderConfigModel(BaseModel):
    """One LLM provider/deployment."""

    model_config = ConfigDict(extra="ignore")

    provider: str
    model: str
    api_key: str | None = None
    api_key_env: str | None = None
    base_url: str | None = None
    timeout_seconds: float = 60.0
    max_retries: int = 2
    rpm: int | None = None
    tpm: int | None = None
    supports_json_mode: bool | None = None
    supports_reasoning: bool | None = None
    supports_streaming: bool | None = None
    max_output_tokens: int = 2048
    input_cost_per_million_tokens: float | None = None
    output_cost_per_million_tokens: float | None = None

    @field_validator("provider")
    @classmethod
    def provider_known(cls, v: str) -> str:
        allowed = {
            "openai",
            "anthropic",
            "openrouter",
            "openai_compatible",
            "ollama",
        }
        if v not in allowed:
            msg = f"Unknown provider type: {v}"
            raise ValueError(msg)
        return v


class NestedTranslatorConfig(BaseModel):
    """Subset of ``[doctranslate]`` for translator routing (loaded from raw TOML)."""

    model_config = ConfigDict(extra="ignore")

    translator: str = "openai"
    routing_profile: str = "translate"
    term_extraction_profile: str = "terms"
    routing_strategy: RouterStrategy | None = None
    profiles: dict[str, RouteProfileConfig] = Field(default_factory=dict)
    providers: dict[str, ProviderConfigModel] = Field(default_factory=dict)
    metrics_output: str = "log"
    metrics_json_path: str = ""

    @field_validator("routing_strategy", mode="before")
    @classmethod
    def _coerce_global_strategy(cls, v: Any) -> Any:
        if v is None or v == "":
            return None
        if isinstance(v, RouterStrategy):
            return v
        return RouterStrategy(str(v))


def load_nested_translator_config(config_path: Path | None) -> NestedTranslatorConfig:
    """Load ``[doctranslate]`` nested ``profiles`` / ``providers`` from a TOML file."""
    if not config_path or not Path(config_path).exists():
        return NestedTranslatorConfig()
    data = toml.load(Path(config_path))
    dt = data.get("doctranslate")
    if not isinstance(dt, dict):
        return NestedTranslatorConfig()
    return NestedTranslatorConfig.model_validate(_coerce_doctranslate_table(dt))


def _coerce_doctranslate_table(dt: dict[str, Any]) -> dict[str, Any]:
    """Normalize keys for Pydantic (already nested from TOML)."""
    out: dict[str, Any] = {
        "translator": dt.get("translator", "openai"),
        "routing_profile": dt.get("routing_profile", "translate"),
        "term_extraction_profile": dt.get("term_extraction_profile", "terms"),
        "metrics_output": dt.get("metrics_output", "log"),
        "metrics_json_path": dt.get("metrics_json_path", ""),
    }
    if dt.get("routing_strategy") is not None:
        out["routing_strategy"] = dt.get("routing_strategy")
    profiles = dt.get("profiles")
    if isinstance(profiles, dict):
        out["profiles"] = profiles
    providers = dt.get("providers")
    if isinstance(providers, dict):
        out["providers"] = providers
    return out


def resolve_provider_api_key(cfg: ProviderConfigModel) -> str | None:
    """Resolve API key from inline config or environment."""
    if cfg.api_key:
        return cfg.api_key
    if cfg.api_key_env:
        return os.environ.get(cfg.api_key_env)
    return None


def merge_cli_router_overrides(
    nested: NestedTranslatorConfig,
    *,
    routing_profile: str | None = None,
    term_extraction_profile: str | None = None,
    routing_strategy: RouterStrategy | str | None = None,
    metrics_output: str | None = None,
    metrics_json_path: str | None = None,
) -> NestedTranslatorConfig:
    """Apply CLI overrides onto a nested config copy."""
    data = nested.model_dump()
    if routing_profile is not None:
        data["routing_profile"] = routing_profile
    if term_extraction_profile is not None:
        data["term_extraction_profile"] = term_extraction_profile
    if routing_strategy is not None:
        if isinstance(routing_strategy, RouterStrategy):
            data["routing_strategy"] = routing_strategy
        else:
            data["routing_strategy"] = RouterStrategy(str(routing_strategy))
    if metrics_output is not None:
        data["metrics_output"] = metrics_output
    if metrics_json_path is not None:
        data["metrics_json_path"] = metrics_json_path
    return NestedTranslatorConfig.model_validate(data)


def merge_cli_router_overrides_from_mapping(
    nested: NestedTranslatorConfig,
    overrides: dict[str, Any] | None,
) -> NestedTranslatorConfig:
    """Apply only keys present in ``overrides`` (values may not be None)."""
    if not overrides:
        return nested
    kwargs: dict[str, Any] = {}
    if "routing_profile" in overrides:
        kwargs["routing_profile"] = overrides["routing_profile"]
    if "term_extraction_profile" in overrides:
        kwargs["term_extraction_profile"] = overrides["term_extraction_profile"]
    if "routing_strategy" in overrides:
        kwargs["routing_strategy"] = overrides["routing_strategy"]
    if "metrics_output" in overrides:
        kwargs["metrics_output"] = overrides["metrics_output"]
    if "metrics_json_path" in overrides:
        kwargs["metrics_json_path"] = overrides["metrics_json_path"]
    return merge_cli_router_overrides(nested, **kwargs)


def validate_router_config(cfg: NestedTranslatorConfig) -> None:
    """Validate profiles reference existing provider ids."""
    for pname, prof in cfg.profiles.items():
        for pid in prof.providers:
            if pid not in cfg.providers:
                msg = f"Profile {pname!r} references unknown provider id {pid!r}"
                raise ValueError(msg)
    for pname, prof in cfg.profiles.items():
        if prof.require_json_mode:
            for pid in prof.providers:
                p = cfg.providers[pid]
                eff = _effective_supports_json(p)
                if not eff:
                    msg = (
                        f"Profile {pname!r} requires JSON mode but provider {pid!r} "
                        "does not enable supports_json_mode"
                    )
                    raise ValueError(msg)


def _effective_supports_json(p: ProviderConfigModel) -> bool:
    if p.supports_json_mode is not None:
        return bool(p.supports_json_mode)
    return p.provider in (
        "openai",
        "anthropic",
        "openrouter",
        "openai_compatible",
        "ollama",
    )
