"""HTTP API authentication (shared secret)."""

from __future__ import annotations

from pathlib import Path

import pytest
from doctranslate.http_api.settings import get_settings
from fastapi.testclient import TestClient


@pytest.fixture
def api_client_auth_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    monkeypatch.setenv("DOCTRANSLATE_API_DATA_ROOT", str(tmp_path / "api-data"))
    monkeypatch.setenv("DOCTRANSLATE_API_AUTH_MODE", "required")
    monkeypatch.setenv("DOCTRANSLATE_API_AUTH_TOKEN", "test-secret-token")
    monkeypatch.setenv("DOCTRANSLATE_METRICS_ENABLED", "false")
    get_settings.cache_clear()
    from doctranslate.http_api.app import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client
    get_settings.cache_clear()


@pytest.fixture
def api_client_probes_need_auth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    monkeypatch.setenv("DOCTRANSLATE_API_DATA_ROOT", str(tmp_path / "api-data"))
    monkeypatch.setenv("DOCTRANSLATE_API_AUTH_MODE", "required")
    monkeypatch.setenv("DOCTRANSLATE_API_AUTH_TOKEN", "probe-secret")
    monkeypatch.setenv(
        "DOCTRANSLATE_API_AUTH_ALLOW_UNAUTHENTICATED_PROBE_PATHS", "false"
    )
    monkeypatch.setenv("DOCTRANSLATE_METRICS_ENABLED", "false")
    get_settings.cache_clear()
    from doctranslate.http_api.app import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client
    get_settings.cache_clear()


def test_jobs_401_without_credentials(api_client_auth_required: TestClient) -> None:
    r = api_client_auth_required.post(
        "/v1/jobs",
        data={"translation_request": "{}"},
    )
    assert r.status_code == 401
    body = r.json()
    assert body.get("ok") is False


def test_jobs_401_bad_token(api_client_auth_required: TestClient) -> None:
    r = api_client_auth_required.post(
        "/v1/jobs",
        data={"translation_request": "{}"},
        headers={"Authorization": "Bearer wrong"},
    )
    assert r.status_code == 401


def test_runtime_200_with_bearer(api_client_auth_required: TestClient) -> None:
    r = api_client_auth_required.get(
        "/v1/runtime",
        headers={"Authorization": "Bearer test-secret-token"},
    )
    assert r.status_code == 200
    assert r.json()["app"] == "doctranslate-http-api"


def test_runtime_200_with_api_key_header(api_client_auth_required: TestClient) -> None:
    r = api_client_auth_required.get(
        "/v1/runtime",
        headers={"X-API-Key": "test-secret-token"},
    )
    assert r.status_code == 200


def test_health_live_public_when_probes_allowed(
    api_client_auth_required: TestClient,
) -> None:
    r = api_client_auth_required.get("/v1/health/live")
    assert r.status_code == 200


def test_health_ready_public_when_probes_allowed(
    api_client_auth_required: TestClient,
) -> None:
    r = api_client_auth_required.get("/v1/health/ready")
    assert r.status_code == 200


def test_health_live_requires_auth_when_probes_locked(
    api_client_probes_need_auth: TestClient,
) -> None:
    r = api_client_probes_need_auth.get("/v1/health/live")
    assert r.status_code == 401


def test_openapi_security_on_jobs_not_on_health_live(
    api_client_auth_required: TestClient,
) -> None:
    r = api_client_auth_required.get("/openapi.json")
    assert r.status_code == 401
    r2 = api_client_auth_required.get(
        "/openapi.json",
        headers={"Authorization": "Bearer test-secret-token"},
    )
    assert r2.status_code == 200
    spec = r2.json()
    paths = spec.get("paths", {})
    assert "/v1/jobs" in paths
    assert "/v1/health/live" in paths
    jobs_post = paths.get("/v1/jobs", {}).get("post", {})
    live_get = paths.get("/v1/health/live", {}).get("get", {})
    assert isinstance(jobs_post, dict) and jobs_post
    assert isinstance(live_get, dict) and live_get
