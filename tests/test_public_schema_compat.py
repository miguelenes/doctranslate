"""Golden / compatibility fixtures for public schema v1."""

from __future__ import annotations

import json

from doctranslate.schemas import PUBLIC_SCHEMA_VERSION
from doctranslate.schemas import TranslationRequest


def test_translation_request_v1_fixture() -> None:
    """Pinned v1 payload — bump intentionally when PUBLIC_SCHEMA_VERSION increments."""
    fixture = {
        "schema_version": "1",
        "input_pdf": "doc.pdf",
        "lang_in": "en",
        "lang_out": "fr",
        "translator": {
            "mode": "openai",
            "ignore_cache": False,
            "openai": {"model": "gpt-4o-mini", "api_key": None},
        },
        "options": {"qps": 2, "debug": False},
    }
    assert fixture["schema_version"] == PUBLIC_SCHEMA_VERSION
    req = TranslationRequest.model_validate(fixture)
    assert req.options is not None
    assert req.options.qps == 2
    # Stable JSON keys for external repos
    dumped = json.loads(req.model_dump_json())
    assert dumped["schema_version"] == "1"
