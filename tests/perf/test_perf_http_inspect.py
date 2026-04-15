"""HTTP ``/v1/inspect`` latency (in-process TestClient)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("fastapi")

pytestmark = [
    pytest.mark.perf,
    pytest.mark.requires_pdf,
    pytest.mark.requires_full,
]


@pytest.fixture
def api_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    root = tmp_path / "api-data"
    monkeypatch.setenv("DOCTRANSLATE_API_DATA_ROOT", str(root))
    monkeypatch.setenv(
        "DOCTRANSLATE_API_MOUNT_ALLOW_PREFIXES",
        str(Path(__file__).resolve().parents[2]),
    )
    from doctranslate.http_api.settings import get_settings

    get_settings.cache_clear()
    from doctranslate.http_api.app import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client
    get_settings.cache_clear()


@pytest.mark.perf
def test_perf_http_inspect_pdf(benchmark, api_client: TestClient, ci_test_pdf: Path):
    """POST ``/v1/inspect`` for the CI sample PDF."""

    def _call():
        r = api_client.post("/v1/inspect", json={"paths": [str(ci_test_pdf)]})
        assert r.status_code == 200
        return r.json()

    data = benchmark(_call)
    assert data["schema_version"] == "1"
    assert len(data["files"]) == 1
