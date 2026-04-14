"""Build ``OpenAITranslator`` or ``TranslatorRouter`` from CLI args and nested TOML."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from doctranslate.translator.config import NestedTranslatorConfig
from doctranslate.translator.config import ProviderConfigModel
from doctranslate.translator.config import load_nested_translator_config
from doctranslate.translator.config import merge_cli_router_overrides_from_mapping
from doctranslate.translator.config import resolve_provider_api_key
from doctranslate.translator.config import validate_router_config
from doctranslate.translator.translator import OpenAITranslator
from doctranslate.translator.types import TranslatorCapabilities

logger = logging.getLogger(__name__)


def _provider_requires_resolved_api_key(cfg: ProviderConfigModel) -> bool:
    """Hosted providers that must have an API key (local Ollama / openai_compatible exempt)."""
    return cfg.provider in ("openai", "anthropic", "openrouter")


@dataclass
class TranslatorBuildResult:
    """Translators for main PDF path and optional separate term-extraction path."""

    translator: Any
    term_extraction_translator: Any
    nested_config: NestedTranslatorConfig | None


def _default_capabilities_for_provider(
    provider_id: str,
    cfg: ProviderConfigModel,
) -> TranslatorCapabilities:
    """Infer capabilities when TOML omits explicit flags."""
    sj = cfg.supports_json_mode
    if sj is None:
        sj = cfg.provider in (
            "openai",
            "anthropic",
            "openrouter",
            "openai_compatible",
            "ollama",
        )
    sr = cfg.supports_reasoning
    if sr is None:
        sr = cfg.provider in ("openai", "anthropic", "openrouter", "openai_compatible")
    ss = cfg.supports_streaming
    if ss is None:
        ss = False
    s_struct = cfg.supports_structured_outputs
    if s_struct is None:
        s_struct = cfg.provider in (
            "openai",
            "anthropic",
            "openrouter",
            "openai_compatible",
            "ollama",
        )
    supports_resp: bool | None = None
    if cfg.provider == "openai":
        supports_resp = cfg.base_url is None
    return TranslatorCapabilities(
        supports_llm=True,
        supports_json_mode=bool(sj),
        supports_reasoning=bool(sr),
        supports_streaming=bool(ss),
        supports_structured_outputs=bool(s_struct),
        supports_responses_api=supports_resp,
        max_output_tokens=cfg.max_output_tokens,
        rpm=cfg.rpm,
        tpm=cfg.tpm,
        provider_id=provider_id,
    )


def build_translators_from_openai_cli(
    *,
    lang_in: str,
    lang_out: str,
    ignore_cache: bool,
    model: str,
    base_url: str | None,
    api_key: str | None,
    enable_json_mode_if_requested: bool,
    send_dashscope_header: bool,
    send_temperature: bool,
    reasoning: str | None,
    term_model: str | None,
    term_base_url: str | None,
    term_api_key: str | None,
    term_reasoning: str | None,
) -> TranslatorBuildResult:
    """Legacy path: one or two ``OpenAITranslator`` instances."""
    kwargs: dict[str, Any] = {}
    if reasoning is not None:
        kwargs["reasoning"] = reasoning
    translator = OpenAITranslator(
        lang_in=lang_in,
        lang_out=lang_out,
        model=model,
        base_url=base_url,
        api_key=api_key,
        ignore_cache=ignore_cache,
        enable_json_mode_if_requested=enable_json_mode_if_requested,
        send_dashscope_header=send_dashscope_header,
        send_temperature=send_temperature,
        **kwargs,
    )
    term_extraction_translator = translator
    if term_model or term_base_url or term_api_key:
        tk: dict[str, Any] = {}
        if term_reasoning is not None:
            tk["reasoning"] = term_reasoning
        term_extraction_translator = OpenAITranslator(
            lang_in=lang_in,
            lang_out=lang_out,
            model=term_model or model,
            base_url=term_base_url or base_url,
            api_key=term_api_key or api_key,
            ignore_cache=ignore_cache,
            enable_json_mode_if_requested=enable_json_mode_if_requested,
            send_dashscope_header=send_dashscope_header,
            send_temperature=send_temperature,
            **tk,
        )
    return TranslatorBuildResult(
        translator=translator,
        term_extraction_translator=term_extraction_translator,
        nested_config=None,
    )


def build_translators_from_router_config(
    *,
    lang_in: str,
    lang_out: str,
    ignore_cache: bool,
    nested: NestedTranslatorConfig,
) -> TranslatorBuildResult:
    """Router path: two ``TranslatorRouter`` instances (translate + term extraction)."""
    from doctranslate.translator.providers.litellm_provider import (
        LiteLLMProviderExecutor,
    )
    from doctranslate.translator.router import TranslatorRouter

    validate_router_config(nested)
    translate_profile = nested.profiles.get(nested.routing_profile)
    if not translate_profile or not translate_profile.providers:
        msg = f"Missing or empty routing profile {nested.routing_profile!r}"
        raise ValueError(msg)
    terms_profile = nested.profiles.get(nested.term_extraction_profile)
    if not terms_profile or not terms_profile.providers:
        msg = f"Missing or empty term extraction profile {nested.term_extraction_profile!r}"
        raise ValueError(msg)

    strategy = nested.routing_strategy or translate_profile.strategy

    executors: dict[str, Any] = {}
    cap_map: dict[str, TranslatorCapabilities] = {}
    for pid, pcfg in nested.providers.items():
        if _provider_requires_resolved_api_key(pcfg) and not resolve_provider_api_key(
            pcfg
        ):
            env_hint = pcfg.api_key_env or "(inline api_key)"
            msg = f"Provider {pid!r} has no API key (check env {env_hint})"
            raise ValueError(msg)
        executors[pid] = LiteLLMProviderExecutor(pid, pcfg)
        cap_map[pid] = _default_capabilities_for_provider(pid, pcfg)

    translator = TranslatorRouter(
        lang_in=lang_in,
        lang_out=lang_out,
        ignore_cache=ignore_cache,
        profile_name=nested.routing_profile,
        route_profile=translate_profile,
        global_strategy=strategy,
        executors=executors,
        capabilities_by_id=cap_map,
        provider_configs=nested.providers,
        nested_settings=nested,
    )
    term_strategy = nested.routing_strategy or terms_profile.strategy
    term_extraction_translator = TranslatorRouter(
        lang_in=lang_in,
        lang_out=lang_out,
        ignore_cache=ignore_cache,
        profile_name=nested.term_extraction_profile,
        route_profile=terms_profile,
        global_strategy=term_strategy,
        executors=executors,
        capabilities_by_id=cap_map,
        provider_configs=nested.providers,
        nested_settings=nested,
    )
    return TranslatorBuildResult(
        translator=translator,
        term_extraction_translator=term_extraction_translator,
        nested_config=nested,
    )


def resolve_openai_api_key(cli_key: str | None) -> str | None:
    """OpenAI API key from CLI or ``OPENAI_API_KEY``."""
    return cli_key or os.environ.get("OPENAI_API_KEY")


def build_translators(
    *,
    translator_mode: str,
    config_path: Any,
    lang_in: str,
    lang_out: str,
    ignore_cache: bool,
    openai_args: dict[str, Any] | None = None,
    cli_router_overrides: dict[str, Any] | None = None,
    local_cli: dict[str, Any] | None = None,
) -> TranslatorBuildResult:
    """Dispatch between legacy OpenAI CLI, multi-provider router, and local mode."""
    if translator_mode == "openai":
        oa = openai_args or {}
        return build_translators_from_openai_cli(
            lang_in=lang_in,
            lang_out=lang_out,
            ignore_cache=ignore_cache,
            **oa,
        )
    if translator_mode == "router":
        nested = load_nested_translator_config(
            Path(config_path) if config_path else None,
        )
        if cli_router_overrides:
            nested = merge_cli_router_overrides_from_mapping(
                nested, cli_router_overrides
            )
        return build_translators_from_router_config(
            lang_in=lang_in,
            lang_out=lang_out,
            ignore_cache=ignore_cache,
            nested=nested,
        )
    if translator_mode == "local":
        from doctranslate.translator.local_config import (
            convert_local_translator_to_router_nested,
        )
        from doctranslate.translator.local_config import merge_local_cli_into_nested

        nested = load_nested_translator_config(
            Path(config_path) if config_path else None,
        )
        nested = merge_local_cli_into_nested(nested, local_cli or {})
        nested = nested.model_copy(update={"translator": "local"})
        nested = convert_local_translator_to_router_nested(nested)
        if cli_router_overrides:
            nested = merge_cli_router_overrides_from_mapping(
                nested, cli_router_overrides
            )
        return build_translators_from_router_config(
            lang_in=lang_in,
            lang_out=lang_out,
            ignore_cache=ignore_cache,
            nested=nested,
        )
    msg = f"Unknown translator mode: {translator_mode}"
    raise ValueError(msg)
