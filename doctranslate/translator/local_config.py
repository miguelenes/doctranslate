"""Local translation mode: build router-shaped config from ``[doctranslate]`` + CLI."""

from __future__ import annotations

from typing import Any

from doctranslate.translator.config import NestedTranslatorConfig
from doctranslate.translator.config import ProviderConfigModel
from doctranslate.translator.config import RouteProfileConfig
from doctranslate.translator.config import RouterStrategy

LOCAL_DEFAULT_OLLAMA_BASE = "http://127.0.0.1:11434"
LOCAL_DEFAULT_VLLM_BASE = "http://127.0.0.1:8000/v1"


def _normalize_backend_name(backend: str | None) -> str:
    b = (backend or "ollama").lower().replace("_", "-")
    if b == "openai_compatible":
        return "openai-compatible"
    return b


def _normalize_openai_compatible_base_url(url: str) -> str:
    u = url.rstrip("/")
    if not u.endswith("/v1"):
        u = f"{u}/v1"
    return u


def _backend_requires_base_url(backend: str) -> bool:
    return backend in ("vllm", "llama-cpp", "openai-compatible")


def merge_local_cli_into_nested(
    nested: NestedTranslatorConfig,
    cli: dict[str, Any],
) -> NestedTranslatorConfig:
    """Apply only non-None keys from ``cli`` onto nested local fields."""
    data = nested.model_dump()
    for k, v in cli.items():
        if v is None:
            continue
        if k in data:
            data[k] = v
    return NestedTranslatorConfig.model_validate(data)


def nested_from_local_cli_mapping(cli: dict[str, Any]) -> NestedTranslatorConfig:
    """Build a minimal nested config for ``--translator local`` without a TOML file."""
    return NestedTranslatorConfig.model_validate(
        {
            "translator": "local",
            **{k: v for k, v in cli.items() if v is not None},
        },
    )


def _make_translate_provider(nested: NestedTranslatorConfig) -> ProviderConfigModel:
    backend = _normalize_backend_name(nested.local_backend)
    timeout = (
        nested.local_timeout_seconds
        if nested.local_timeout_seconds is not None
        else 120.0
    )
    max_retries = (
        nested.local_max_retries if nested.local_max_retries is not None else 2
    )
    model = (nested.local_model or "").strip()
    if not model:
        msg = "local_model is required for local translation"
        raise ValueError(msg)

    if backend == "ollama":
        base = (nested.local_base_url or LOCAL_DEFAULT_OLLAMA_BASE).rstrip("/")
        return ProviderConfigModel(
            provider="ollama",
            model=model,
            base_url=base,
            timeout_seconds=timeout,
            max_retries=max_retries,
            supports_json_mode=True,
        )

    if backend in ("vllm", "llama-cpp", "openai-compatible"):
        if backend == "vllm" and not nested.local_base_url:
            base_url = _normalize_openai_compatible_base_url(LOCAL_DEFAULT_VLLM_BASE)
        elif not nested.local_base_url:
            msg = f"local_base_url is required for local backend {backend!r}"
            raise ValueError(msg)
        else:
            base_url = _normalize_openai_compatible_base_url(nested.local_base_url)
        api_key = (nested.local_api_key or "").strip() or None
        return ProviderConfigModel(
            provider="openai_compatible",
            model=model,
            base_url=base_url,
            api_key=api_key or "EMPTY",
            timeout_seconds=timeout,
            max_retries=max_retries,
            supports_json_mode=True,
        )

    if backend == "ctranslate2":
        msg = "CTranslate2 local backend is not implemented yet; use ollama, vllm, llama-cpp, or openai-compatible"
        raise ValueError(msg)

    msg = f"Unknown local_backend: {backend!r}"
    raise ValueError(msg)


def _make_term_provider(nested: NestedTranslatorConfig) -> ProviderConfigModel:
    """Term extraction provider; may differ from paragraph provider."""
    term_model = (nested.local_term_model or nested.local_model or "").strip()
    if not term_model:
        msg = "local_model (or local_term_model) is required"
        raise ValueError(msg)

    backend = _normalize_backend_name(nested.local_backend)
    timeout = (
        nested.local_timeout_seconds
        if nested.local_timeout_seconds is not None
        else 120.0
    )
    max_retries = (
        nested.local_max_retries if nested.local_max_retries is not None else 2
    )

    if backend == "ollama":
        base = (
            nested.local_term_base_url
            or nested.local_base_url
            or LOCAL_DEFAULT_OLLAMA_BASE
        ).rstrip("/")
        return ProviderConfigModel(
            provider="ollama",
            model=term_model,
            base_url=base,
            timeout_seconds=timeout,
            max_retries=max_retries,
            supports_json_mode=True,
        )

    if backend in ("vllm", "llama-cpp", "openai-compatible"):
        raw = nested.local_term_base_url or nested.local_base_url
        if not raw:
            msg = "local_base_url (or local_term_base_url) is required for this local backend"
            raise ValueError(msg)
        base_url = _normalize_openai_compatible_base_url(raw)
        api_key = (nested.local_api_key or "").strip() or None
        return ProviderConfigModel(
            provider="openai_compatible",
            model=term_model,
            base_url=base_url,
            api_key=api_key or "EMPTY",
            timeout_seconds=timeout,
            max_retries=max_retries,
            supports_json_mode=True,
        )

    if backend == "ctranslate2":
        msg = "CTranslate2 local backend is not implemented yet"
        raise ValueError(msg)

    msg = f"Unknown local_backend: {backend!r}"
    raise ValueError(msg)


def convert_local_translator_to_router_nested(
    nested: NestedTranslatorConfig,
) -> NestedTranslatorConfig:
    """Expand ``translator=\"local\"`` into a synthetic router config for ``build_translators_from_router_config``."""
    if nested.translator != "local":
        return nested

    translate_p = _make_translate_provider(nested)
    term_p = _make_term_provider(nested)

    providers: dict[str, ProviderConfigModel] = {
        "local_translate": translate_p,
        "local_terms": term_p,
    }

    strategy = nested.routing_strategy or RouterStrategy.FAILOVER
    profiles: dict[str, RouteProfileConfig] = {
        "translate": RouteProfileConfig(
            providers=["local_translate"],
            strategy=strategy,
            require_json_mode=False,
        ),
        "terms": RouteProfileConfig(
            providers=["local_terms"],
            strategy=strategy,
            require_json_mode=True,
        ),
    }

    return NestedTranslatorConfig(
        translator="router",
        routing_profile=nested.routing_profile or "translate",
        term_extraction_profile=nested.term_extraction_profile or "terms",
        routing_strategy=nested.routing_strategy,
        profiles=profiles,
        providers=providers,
        metrics_output=nested.metrics_output,
        metrics_json_path=nested.metrics_json_path,
        local_backend=nested.local_backend,
        local_model=nested.local_model,
        local_base_url=nested.local_base_url,
        local_term_model=nested.local_term_model,
        local_term_base_url=nested.local_term_base_url,
        local_api_key=nested.local_api_key,
        local_timeout_seconds=nested.local_timeout_seconds,
        local_max_retries=nested.local_max_retries,
        local_context_window=nested.local_context_window,
        local_translation_batch_tokens=nested.local_translation_batch_tokens,
        local_translation_batch_paragraphs=nested.local_translation_batch_paragraphs,
        local_term_batch_tokens=nested.local_term_batch_tokens,
        local_term_batch_paragraphs=nested.local_term_batch_paragraphs,
    )


def local_cli_dict_from_args(args: Any) -> dict[str, Any]:
    """Extract local-related fields from argparse namespace."""
    keys = (
        "local_backend",
        "local_model",
        "local_base_url",
        "local_term_model",
        "local_term_base_url",
        "local_api_key",
        "local_timeout_seconds",
        "local_max_retries",
        "local_context_window",
        "local_translation_batch_tokens",
        "local_translation_batch_paragraphs",
        "local_term_batch_tokens",
        "local_term_batch_paragraphs",
    )
    out: dict[str, Any] = {}
    for k in keys:
        if hasattr(args, k):
            v = getattr(args, k)
            if v is not None:
                out[k] = v
    return out


def validate_local_nested(nested: NestedTranslatorConfig) -> str | None:
    """Return an error message string if local settings are invalid, else None."""
    if nested.translator != "local":
        return None
    backend = _normalize_backend_name(nested.local_backend)
    if backend == "ctranslate2":
        return (
            "CTranslate2 is not supported in this version; use ollama, vllm, "
            "llama-cpp, or openai-compatible."
        )
    if not (nested.local_model or "").strip():
        return "Local mode requires --local-model (or local_model in config TOML)."
    if _backend_requires_base_url(backend) and not nested.local_base_url:
        return f"Local backend {backend!r} requires --local-base-url (or local_base_url in config)."
    if backend not in (
        "ollama",
        "vllm",
        "llama-cpp",
        "openai-compatible",
        "openai_compatible",
    ):
        return f"Unknown --local-backend: {backend!r}"
    return None
