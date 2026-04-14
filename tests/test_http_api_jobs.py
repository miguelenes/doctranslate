"""HTTP API job creation validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from doctranslate.http_api.settings import get_settings
from fastapi.testclient import TestClient

pytestmark = pytest.mark.requires_full


@pytest.fixture
def api_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DOCTRANSLATE_API_DATA_ROOT", str(tmp_path / "api-data"))
    get_settings.cache_clear()
    from doctranslate.http_api.app import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client
    get_settings.cache_clear()


def test_jobs_invalid_json_form(api_client: TestClient) -> None:
    r = api_client.post(
        "/v1/jobs",
        data={"translation_request": "not-json{"},
        files={"input_pdf": ("x.pdf", b"%PDF-1.4\n", "application/pdf")},
    )
    assert r.status_code == 400
    body = r.json()
    assert body.get("ok") is False


def test_jobs_missing_input_without_file(api_client: TestClient) -> None:
    payload = {
        "schema_version": "1",
        "lang_in": "en",
        "lang_out": "zh",
        "translator": {"mode": "openai", "openai": {"model": "gpt-4o-mini"}},
    }
    r = api_client.post(
        "/v1/jobs",
        data={"translation_request": json.dumps(payload)},
    )
    assert r.status_code == 400
