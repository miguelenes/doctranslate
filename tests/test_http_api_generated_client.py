"""End-to-end smoke: generated OpenAPI client + ASGI transport."""

from __future__ import annotations

import base64
from collections.abc import Generator
from http import HTTPStatus
from pathlib import Path

import pytest
from doc_translater_http_api_client import Client
from doc_translater_http_api_client import wait_until_terminal_sync
from doc_translater_http_api_client.api.jobs import v1_jobs_create_json
from doc_translater_http_api_client.api.jobs import v1_jobs_manifest_get
from doc_translater_http_api_client.models.job_create_json_body import JobCreateJsonBody
from doc_translater_http_api_client.models.translation_request import TranslationRequest
from starlette.testclient import TestClient


@pytest.fixture
def asgi_http_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[Client]:
    root = tmp_path / "api-data"
    monkeypatch.setenv("DOCTRANSLATE_API_DATA_ROOT", str(root))
    from doctranslate.http_api.settings import get_settings

    get_settings.cache_clear()
    from doctranslate.http_api.app import create_app

    app = create_app()
    base = "http://test"
    with TestClient(app, base_url=base) as raw:
        client = Client(base_url=base, timeout=120.0)
        client.set_httpx_client(raw)
        client.raise_on_unexpected_status = True
        yield client
    get_settings.cache_clear()


def _ci_pdf() -> Path:
    p = Path(__file__).resolve().parents[1] / "examples" / "ci" / "test.pdf"
    assert p.is_file()
    return p


def test_generated_client_create_json_wait_manifest(
    asgi_http_client: Client,
) -> None:
    pdf = _ci_pdf()
    b64 = base64.standard_b64encode(pdf.read_bytes()).decode("ascii")
    tr_dict = {
        "schema_version": "1",
        "lang_in": "en",
        "lang_out": "zh",
        "input_pdf": "",
        "translator": {"mode": "openai", "openai": {"model": "gpt-4o-mini"}},
        # ``only_parse_generate_pdf`` short-circuits heavy layout stages in CI; keep
        # ``skip_translation`` so the job still exercises the public JSON shape.
        "options": {
            "skip_translation": True,
            "only_parse_generate_pdf": True,
        },
    }
    tr = TranslationRequest.from_dict(tr_dict)
    body = JobCreateJsonBody(translation_request=tr, input_pdf_base64=b64)
    created = v1_jobs_create_json.sync_detailed(client=asgi_http_client, body=body)
    assert created.status_code == HTTPStatus.ACCEPTED
    assert created.parsed is not None
    job_id = created.parsed.job_id
    final = wait_until_terminal_sync(
        client=asgi_http_client,
        job_id=job_id,
        timeout_s=120.0,
    )
    assert final.state == "succeeded"
    man = v1_jobs_manifest_get.sync_detailed(job_id=job_id, client=asgi_http_client)
    assert man.status_code == HTTPStatus.OK
    assert man.parsed is not None
    assert man.parsed.items
