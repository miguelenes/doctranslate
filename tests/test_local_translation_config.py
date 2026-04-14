"""Tests for local translator TOML/CLI merge and synthetic router expansion."""

from pathlib import Path

import pytest

from doctranslate.translator.config import NestedTranslatorConfig, load_nested_translator_config
from doctranslate.translator.local_config import (
    convert_local_translator_to_router_nested,
    merge_local_cli_into_nested,
    validate_local_nested,
)


def test_validate_local_requires_model():
    n = NestedTranslatorConfig(translator="local", local_backend="ollama")
    err = validate_local_nested(n)
    assert err is not None
    assert "local-model" in err or "local_model" in err


def test_convert_ollama_to_router_nested():
    n = NestedTranslatorConfig(
        translator="local",
        local_backend="ollama",
        local_model="qwen2.5:7b",
        local_base_url="http://127.0.0.1:11434",
    )
    assert validate_local_nested(n) is None
    r = convert_local_translator_to_router_nested(n)
    assert r.translator == "router"
    assert "local_translate" in r.providers
    assert r.providers["local_translate"].provider == "ollama"
    assert r.providers["local_translate"].model == "qwen2.5:7b"


def test_merge_local_cli_overrides_toml(tmp_path: Path):
    p = tmp_path / "c.toml"
    p.write_text(
        """
[doctranslate]
translator = "local"
local_backend = "ollama"
local_model = "from-file"

[doctranslate.local]
timeout_seconds = 99
""",
        encoding="utf-8",
    )
    nested = load_nested_translator_config(p)
    assert nested.local_timeout_seconds == 99.0
    merged = merge_local_cli_into_nested(
        nested,
        {"local_model": "from-cli", "local_timeout_seconds": 50.0},
    )
    assert merged.local_model == "from-cli"
    assert merged.local_timeout_seconds == 50.0


def test_validate_rejects_ctranslate2_backend():
    n = NestedTranslatorConfig(
        translator="local",
        local_backend="ctranslate2",
        local_model="x",
    )
    err = validate_local_nested(n)
    assert err is not None
    assert "CTranslate2" in err
