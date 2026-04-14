"""Factory builds executors for Ollama providers (no API key)."""

from doctranslate.translator.config import NestedTranslatorConfig
from doctranslate.translator.config import ProviderConfigModel
from doctranslate.translator.config import RouteProfileConfig
from doctranslate.translator.factory import build_translators
from doctranslate.translator.factory import build_translators_from_router_config


def test_build_router_with_ollama_provider():
    nested = NestedTranslatorConfig(
        translator="router",
        routing_profile="translate",
        term_extraction_profile="terms",
        profiles={
            "translate": RouteProfileConfig(
                providers=["ollama_p"], require_json_mode=False
            ),
            "terms": RouteProfileConfig(providers=["ollama_p"], require_json_mode=True),
        },
        providers={
            "ollama_p": ProviderConfigModel(
                provider="ollama",
                model="mistral",
                base_url="http://127.0.0.1:11434",
            ),
        },
    )
    built = build_translators_from_router_config(
        lang_in="en",
        lang_out="zh",
        ignore_cache=True,
        nested=nested,
    )
    assert built.translator is not None
    assert built.term_extraction_translator is not None


def test_build_translators_local_mode_synthetic_router():
    built = build_translators(
        translator_mode="local",
        config_path=None,
        lang_in="en",
        lang_out="zh",
        ignore_cache=True,
        local_cli={
            "local_backend": "ollama",
            "local_model": "qwen2.5:7b",
        },
    )
    assert built.translator.name == "router"
    assert built.nested_config is not None
    assert built.nested_config.providers["local_translate"].provider == "ollama"
