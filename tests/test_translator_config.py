"""Tests for nested translator TOML configuration."""

from pathlib import Path

import pytest
from doctranslate.translator.config import NestedTranslatorConfig
from doctranslate.translator.config import load_nested_translator_config
from doctranslate.translator.config import merge_cli_router_overrides_from_mapping
from doctranslate.translator.config import validate_router_config
from doctranslate.translator.types import RouterStrategy


def test_merge_cli_router_overrides(tmp_path: Path):
    p = tmp_path / "c.toml"
    p.write_text(
        """
[doctranslate]
translator = "router"
routing_profile = "translate"

[doctranslate.profiles.translate]
providers = ["a"]
strategy = "failover"

[doctranslate.providers.a]
provider = "openai"
model = "gpt-4o-mini"
api_key = "sk-test"
""",
        encoding="utf-8",
    )
    nested = load_nested_translator_config(p)
    merged = merge_cli_router_overrides_from_mapping(
        nested,
        {"routing_strategy": "round_robin", "routing_profile": "translate"},
    )
    assert merged.routing_strategy == RouterStrategy.ROUND_ROBIN


def test_validate_router_rejects_unknown_provider():
    from doctranslate.translator.config import RouteProfileConfig

    bad = NestedTranslatorConfig(
        profiles={"x": RouteProfileConfig(providers=["missing"])},
        providers={},
    )
    with pytest.raises(ValueError, match="unknown provider"):
        validate_router_config(bad)


def test_load_nested_ignores_babeldoc_section(tmp_path: Path):
    p = tmp_path / "legacy.toml"
    p.write_text(
        """
[babeldoc]
translator = "router"
""",
        encoding="utf-8",
    )
    nested = load_nested_translator_config(p)
    assert nested.translator == "openai"


def test_validate_json_requirement():
    from doctranslate.translator.config import ProviderConfigModel
    from doctranslate.translator.config import RouteProfileConfig

    cfg = NestedTranslatorConfig(
        profiles={
            "j": RouteProfileConfig(
                providers=["p"],
                require_json_mode=True,
            ),
        },
        providers={
            "p": ProviderConfigModel(
                provider="openai",
                model="gpt-4o-mini",
                api_key="k",
                supports_json_mode=False,
            ),
        },
    )
    with pytest.raises(ValueError, match="JSON"):
        validate_router_config(cfg)
