"""Webhook signing helpers."""

from __future__ import annotations

from doctranslate.http_api.webhook_delivery import sign_standard_webhook_v1


def test_sign_standard_webhook_v1_format() -> None:
    body = b'{"type":"job.terminal"}'
    sig = sign_standard_webhook_v1(
        secret="unit-test-secret",  # noqa: S106
        msg_id="mid",
        ts=1700000000,
        body=body,
    )
    assert sig.startswith("v1,")
    assert len(sig) > 8
