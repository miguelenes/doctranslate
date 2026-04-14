"""Redaction helpers for structured logging."""

from __future__ import annotations

from doctranslate.observability.redaction import redact_string
from doctranslate.observability.redaction import redact_value


def test_redact_nested_secrets() -> None:
    payload = {
        "api_key": "sk-secret",
        "nested": {"Authorization": "Bearer x"},
        "ok": "visible",
    }
    out = redact_value(payload, redact_user_text=True)
    assert out["api_key"] == "<redacted>"
    assert out["nested"]["Authorization"] == "<redacted>"
    assert out["ok"] == "visible"


def test_redact_long_string_truncates_when_user_text() -> None:
    s = "x" * 600
    r = redact_string(s, redact_user_text=True)
    assert len(r) < len(s)
    assert "truncated" in r.lower()


def test_redact_signed_url_param() -> None:
    u = "https://example.com/a?X-Amz-Signature=abc123&foo=1"
    r = redact_string(u, redact_user_text=False)
    assert "abc123" not in r
    assert "<redacted>" in r
