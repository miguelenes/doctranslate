"""Serialization tests for public Pydantic models."""

from __future__ import annotations

import json

from doctranslate.schemas import ArtifactDescriptor
from doctranslate.schemas import ArtifactKind
from doctranslate.schemas import ArtifactManifest
from doctranslate.schemas import PublicErrorCode
from doctranslate.schemas import TranslationErrorPayload
from doctranslate.schemas import TranslationRequest
from doctranslate.schemas import TranslationResult
from doctranslate.schemas import TranslationSummary
from doctranslate.schemas import progress_event_from_dict


def test_translation_request_json_round_trip() -> None:
    raw = {
        "input_pdf": "/path/to/file.pdf",
        "lang_in": "en",
        "lang_out": "zh",
        "translator": {"mode": "router", "config_path": "/x/doctranslate.toml"},
    }
    req = TranslationRequest.model_validate(raw)
    dumped = json.loads(req.model_dump_json())
    req2 = TranslationRequest.model_validate(dumped)
    assert req2.input_pdf == req.input_pdf
    assert req2.translator.mode == req.translator.mode


def test_progress_event_stage_summary_round_trip() -> None:
    ev = progress_event_from_dict(
        {
            "type": "stage_summary",
            "stages": [{"name": "ILCreater", "percent": 0.14}],
            "part_index": 1,
            "total_parts": 1,
        },
    )
    assert ev["type"] == "stage_summary"
    assert ev["schema_version"] == "1"
    assert ev["stages"][0]["name"] == "ILCreater"


def test_translation_result_round_trip() -> None:
    tr = TranslationResult(
        summary=TranslationSummary(original_pdf_path="/in.pdf"),
        artifacts=ArtifactManifest(
            items=[
                ArtifactDescriptor(
                    kind=ArtifactKind.MONO_WATERMARKED_PDF,
                    path="/out/mono.pdf",
                    sha256="ab" * 32,
                    size_bytes=10,
                    media_type="application/pdf",
                ),
            ],
        ),
    )
    tr2 = TranslationResult.model_validate(json.loads(tr.model_dump_json()))
    assert tr2.artifacts.items[0].kind == ArtifactKind.MONO_WATERMARKED_PDF


def test_translation_error_payload_enum() -> None:
    err = TranslationErrorPayload(
        code=PublicErrorCode.VALIDATION_ERROR,
        message="bad",
    )
    data = json.loads(err.model_dump_json())
    assert data["code"] == "validation_error"
