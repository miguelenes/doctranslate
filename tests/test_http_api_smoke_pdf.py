"""HTTP API smoke against a tracked PDF (no translation)."""

from __future__ import annotations

from pathlib import Path

import pytest
from doctranslate.http_api.settings import get_settings
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.requires_pdf, pytest.mark.requires_full]


@pytest.fixture
def api_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    root = tmp_path / "api-data"
    monkeypatch.setenv("DOCTRANSLATE_API_DATA_ROOT", str(root))
    monkeypatch.setenv(
        "DOCTRANSLATE_API_MOUNT_ALLOW_PREFIXES",
        str(Path(__file__).resolve().parent.parent),
    )
    get_settings.cache_clear()
    from doctranslate.http_api.app import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client
    get_settings.cache_clear()


def test_inspect_pdf(api_client: TestClient, ci_test_pdf: Path) -> None:
    r = api_client.post("/v1/inspect", json={"paths": [str(ci_test_pdf)]})
    assert r.status_code == 200
    data = r.json()
    assert data["schema_version"] == "1"
    assert len(data["files"]) == 1
    assert data["files"][0]["page_count"] >= 1
