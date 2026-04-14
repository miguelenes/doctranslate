"""HTTP API observability: metrics endpoint and request correlation."""

from __future__ import annotations

from pathlib import Path

import pytest
from doctranslate.http_api.settings import get_settings
from doctranslate.observability.config import reset_observability_settings_cache
from fastapi.testclient import TestClient


@pytest.fixture
def api_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    root = tmp_path / "api-data"
    monkeypatch.setenv("DOCTRANSLATE_API_DATA_ROOT", str(root))
    reset_observability_settings_cache()
    get_settings.cache_clear()
    from doctranslate.http_api.app import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client
    get_settings.cache_clear()
    reset_observability_settings_cache()


def test_metrics_endpoint(api_client: TestClient) -> None:
    r = api_client.get("/metrics")
    assert r.status_code == 200
    text = r.text
    assert "#" in text or "HELP" in text or "doctranslate" in text


def test_request_id_on_error_and_header(api_client: TestClient) -> None:
    r = api_client.post(
        "/v1/jobs",
        data={"translation_request": "not-json{"},
        files={"input_pdf": ("x.pdf", b"%PDF-1.4\n", "application/pdf")},
    )
    assert r.status_code == 400
    body = r.json()
    assert body.get("ok") is False
    assert body.get("request_id")
    hdr = r.headers.get("X-Request-ID")
    assert hdr == body["request_id"]
