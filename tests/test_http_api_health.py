"""HTTP API health and runtime endpoints."""

from __future__ import annotations

from pathlib import Path

import pytest
from doctranslate.http_api.settings import get_settings
from fastapi.testclient import TestClient


@pytest.fixture
def api_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    root = tmp_path / "api-data"
    monkeypatch.setenv("DOCTRANSLATE_API_DATA_ROOT", str(root))
    get_settings.cache_clear()
    from doctranslate.http_api.app import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client
    get_settings.cache_clear()


def test_health_live(api_client: TestClient) -> None:
    r = api_client.get("/v1/health/live")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_runtime(api_client: TestClient) -> None:
    r = api_client.get("/v1/runtime")
    assert r.status_code == 200
    data = r.json()
    assert data["app"] == "doctranslate-http-api"
    assert "package_version" in data
    assert data["public_schema_version"] == "1"


def test_health_ready(api_client: TestClient) -> None:
    r = api_client.get("/v1/health/ready")
    assert r.status_code == 200
    body = r.json()
    assert "ready" in body
    assert "checks" in body
    assert body["checks"]["data_root_writable"] is True
    assert body["checks"]["job_queue_healthy"] is True
