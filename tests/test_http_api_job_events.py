"""Job progress events, SSE stream, and manifest."""

from __future__ import annotations

import json
import time
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


def _pdf_path() -> Path:
    repo = Path(__file__).resolve().parents[1]
    p = repo / "examples" / "ci" / "test.pdf"
    assert p.is_file()
    return p


def test_job_events_and_manifest_after_success(api_client: TestClient) -> None:
    pdf = _pdf_path()
    tr = {
        "schema_version": "1",
        "lang_in": "en",
        "lang_out": "zh",
        "translator": {"mode": "openai", "openai": {"model": "gpt-4o-mini"}},
        "options": {"skip_translation": True},
    }
    with pdf.open("rb") as fh:
        r = api_client.post(
            "/v1/jobs",
            data={"translation_request": json.dumps(tr)},
            files={"input_pdf": ("test.pdf", fh, "application/pdf")},
        )
    assert r.status_code == 202, r.text
    job_id = r.json()["job_id"]
    for _ in range(200):
        ev = api_client.get(f"/v1/jobs/{job_id}/events?after_seq=0&limit=50")
        assert ev.status_code == 200
        if ev.json().get("items"):
            break
        time.sleep(0.02)
    ev = api_client.get(f"/v1/jobs/{job_id}/events?after_seq=0&limit=50")
    assert ev.status_code == 200
    body = ev.json()
    assert body["job_id"] == job_id
    assert isinstance(body["items"], list)
    assert len(body["items"]) >= 1
    assert body["items"][-1]["seq"] >= 1

    st = api_client.get(f"/v1/jobs/{job_id}")
    assert st.status_code == 200
    assert st.json().get("progress_seq", 0) >= 1

    res = api_client.get(f"/v1/jobs/{job_id}/result")
    assert res.status_code == 200
    if res.json()["state"] == "succeeded":
        man = api_client.get(f"/v1/jobs/{job_id}/manifest")
        assert man.status_code == 200
        items = man.json()["items"]
        assert items
        kind = items[0]["kind"]
        h = api_client.head(f"/v1/jobs/{job_id}/artifacts/{kind}")
        assert h.status_code == 200
        assert "content-length" in {k.lower() for k in h.headers.keys()}


def test_job_sse_stream_smoke(api_client: TestClient) -> None:
    pdf = _pdf_path()
    tr = {
        "schema_version": "1",
        "lang_in": "en",
        "lang_out": "zh",
        "translator": {"mode": "openai", "openai": {"model": "gpt-4o-mini"}},
        "options": {"skip_translation": True},
    }
    with pdf.open("rb") as fh:
        r = api_client.post(
            "/v1/jobs",
            data={"translation_request": json.dumps(tr)},
            files={"input_pdf": ("test.pdf", fh, "application/pdf")},
        )
    assert r.status_code == 202, r.text
    job_id = r.json()["job_id"]
    with api_client.stream("GET", f"/v1/jobs/{job_id}/stream") as s:
        assert s.status_code == 200
        buf = b""
        for chunk in s.iter_bytes():
            buf += chunk
            if b"job_completed" in buf or b"progress_" in buf or len(buf) > 5000:
                break
        assert buf, "expected non-empty SSE body"
