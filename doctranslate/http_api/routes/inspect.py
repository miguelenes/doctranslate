"""PDF inspection (no translation)."""

from __future__ import annotations

from fastapi import APIRouter

from doctranslate.http_api.models import InspectRequest
from doctranslate.schemas.public_api import InputInspectionResult

router = APIRouter(tags=["inspect"])


@router.post("/v1/inspect", response_model=InputInspectionResult)
def post_inspect(body: InspectRequest) -> InputInspectionResult:
    from doctranslate.api import inspect_input

    return inspect_input(body.paths)
