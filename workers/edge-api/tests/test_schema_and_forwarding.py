"""Tests for edge worker schema imports and multipart forwarding."""

from __future__ import annotations

import asyncio
import io
import json
from typing import Any

import httpx
import pytest
from forwarding import forward_multipart_to_upstream
from forwarding import validate_translation_request_multipart
from starlette.datastructures import FormData
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.testclient import TestClient
from worker import app


def test_import_translation_request_light_path() -> None:
    from doctranslate.schemas.public_api import TranslationRequest
    from doctranslate.schemas.versions import PUBLIC_SCHEMA_VERSION

    assert PUBLIC_SCHEMA_VERSION
    assert TranslationRequest.model_validate(
        {
            "schema_version": PUBLIC_SCHEMA_VERSION,
            "input_pdf": "/work/in.pdf",
            "lang_in": "en",
            "lang_out": "de",
        },
    )


def test_health_and_schema_warmup() -> None:
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        r = client.get("/edge/v1/schema-warmup")
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert body["package"] == "doctranslate.schemas.public_api"
        assert body["schema_version"]


def test_edge_jobs_503_without_upstream() -> None:
    with TestClient(app) as client:
        r = client.post(
            "/edge/v1/jobs",
            data={
                "translation_request": json.dumps(
                    {
                        "schema_version": "1",
                        "input_pdf": "/in.pdf",
                    },
                ),
            },
        )
        assert r.status_code == 503


def test_edge_jobs_502_when_upstream_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import worker as worker_mod
    from doctranslate.schemas.versions import PUBLIC_SCHEMA_VERSION

    async def _fail(**_kwargs: Any) -> None:
        raise httpx.ConnectError(
            "refused",
            request=httpx.Request("POST", "http://upstream.test/v1/jobs"),
        )

    monkeypatch.setattr(worker_mod, "forward_multipart_to_upstream", _fail)
    monkeypatch.setattr(worker_mod, "_upstream_base_url", lambda _env: "http://upstream.test")

    payload = json.dumps(
        {"schema_version": PUBLIC_SCHEMA_VERSION, "input_pdf": "/in.pdf"},
    )
    with TestClient(worker_mod.app) as client:
        r = client.post("/edge/v1/jobs", data={"translation_request": payload})
    assert r.status_code == 502
    assert r.json() == {"detail": "upstream request failed"}


def test_validate_multipart_ok_minimal() -> None:
    from doctranslate.schemas.versions import PUBLIC_SCHEMA_VERSION

    async def _run() -> None:
        payload = json.dumps(
            {"schema_version": PUBLIC_SCHEMA_VERSION, "input_pdf": "/data/in.pdf"},
        )
        form = FormData([("translation_request", payload)])
        tr, extra, pdf = await validate_translation_request_multipart(form)
        assert tr == payload
        assert extra == {}
        assert pdf is None

    asyncio.run(_run())


def test_validate_multipart_rejects_bad_schema_version() -> None:
    async def _run() -> None:
        payload = json.dumps({"schema_version": "999", "input_pdf": "/in.pdf"})
        form = FormData([("translation_request", payload)])
        with pytest.raises(HTTPException) as exc:
            await validate_translation_request_multipart(form)
        assert exc.value.status_code == 400

    asyncio.run(_run())


def test_forward_multipart_mock_upstream() -> None:
    from doctranslate.schemas.versions import PUBLIC_SCHEMA_VERSION

    async def _run() -> None:
        captured: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["content_type"] = request.headers.get("content-type", "")
            captured["auth"] = request.headers.get("authorization")
            return httpx.Response(202, json={"job_id": "edge-test"})

        transport = httpx.MockTransport(handler)
        payload = json.dumps(
            {"schema_version": PUBLIC_SCHEMA_VERSION, "input_pdf": "/in.pdf"},
        )
        raw = io.BytesIO(b"%PDF-1.4 mock")
        up = UploadFile(
            raw,
            filename="doc.pdf",
            headers={"content-type": "application/pdf"},
        )
        form = FormData(
            [
                ("translation_request", payload),
                ("webhook", '{"url":"https://example/hook"}'),
                ("input_pdf", up),
            ],
        )
        tr, extra, pdf = await validate_translation_request_multipart(form)
        assert "webhook" in extra

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://upstream.test",
        ) as client:
            resp = await forward_multipart_to_upstream(
                upstream_jobs_url="http://upstream.test/v1/jobs",
                translation_request_json=tr,
                extra_fields=extra,
                input_pdf=pdf,
                authorization="Bearer unit-test",
                client=client,
            )
        assert resp.status_code == 202
        assert resp.json() == {"job_id": "edge-test"}
        assert "multipart/form-data" in captured["content_type"]
        assert captured["auth"] == "Bearer unit-test"

    asyncio.run(_run())


def test_validate_rejects_duplicate_translation_request() -> None:
    from doctranslate.schemas.versions import PUBLIC_SCHEMA_VERSION

    async def _run() -> None:
        p = json.dumps({"schema_version": PUBLIC_SCHEMA_VERSION, "input_pdf": "/a.pdf"})
        form = FormData(
            [
                ("translation_request", p),
                ("translation_request", p),
            ],
        )
        with pytest.raises(HTTPException) as exc:
            await validate_translation_request_multipart(form)
        assert exc.value.status_code == 400

    asyncio.run(_run())
