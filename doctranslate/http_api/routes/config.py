"""Configuration validation."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi import Depends
from pydantic import ValidationError

from doctranslate.http_api.auth import require_api_operator
from doctranslate.http_api.models import ConfigValidateRequest
from doctranslate.http_api.models import ConfigValidateResponse
from doctranslate.translator.config import load_nested_translator_config
from doctranslate.translator.config import merge_cli_router_overrides_from_mapping
from doctranslate.translator.config import validate_router_config
from doctranslate.translator.providers.local_preflight import LocalPreflightError

router = APIRouter(
    tags=["config"],
    dependencies=[Depends(require_api_operator)],
)


@router.post(
    "/v1/config/validate",
    response_model=ConfigValidateResponse,
    operation_id="v1_config_validate_post",
)
def post_validate_config(body: ConfigValidateRequest) -> ConfigValidateResponse:
    from doctranslate.api import validate_request

    translation_request_valid: bool | None = None
    translator_config_valid: bool | None = None

    if body.translation_request is not None:
        try:
            validate_request(body.translation_request.model_dump(mode="json"))
        except (OSError, ValueError, TypeError, ValidationError):
            translation_request_valid = False
        else:
            translation_request_valid = True

    if body.translator_config is not None:
        spec = body.translator_config
        try:
            if spec.mode == "router":
                nested = load_nested_translator_config(Path(spec.config_path))
                overrides = {
                    k: v
                    for k, v in {
                        "routing_profile": spec.routing_profile,
                        "term_extraction_profile": spec.term_extraction_profile,
                        "routing_strategy": spec.routing_strategy,
                        "metrics_output": spec.metrics_output,
                        "metrics_json_path": spec.metrics_json_path,
                    }.items()
                    if v is not None
                }
                nested = merge_cli_router_overrides_from_mapping(nested, overrides)
                validate_router_config(nested)
            elif spec.mode == "local":
                from doctranslate.translator.local_config import (
                    convert_local_translator_to_router_nested,
                )
                from doctranslate.translator.local_config import (
                    merge_local_cli_into_nested,
                )
                from doctranslate.translator.local_config import validate_local_nested
                from doctranslate.translator.providers.local_preflight import (
                    run_local_preflight,
                )

                nested = load_nested_translator_config(
                    Path(spec.config_path) if spec.config_path else None,
                )
                nested = merge_local_cli_into_nested(
                    nested,
                    spec.local_cli or {},
                )
                nested = nested.model_copy(update={"translator": "local"})
                err = validate_local_nested(nested)
                if err:
                    raise ValueError(err)
                run_local_preflight(nested)
                converted = convert_local_translator_to_router_nested(nested)
                validate_router_config(converted)
            translator_config_valid = True
        except (ValueError, LocalPreflightError, OSError, ValidationError):
            translator_config_valid = False

    ok_parts: list[bool] = []
    if translation_request_valid is not None:
        ok_parts.append(translation_request_valid)
    if translator_config_valid is not None:
        ok_parts.append(translator_config_valid)
    ok = all(ok_parts) if ok_parts else True

    return ConfigValidateResponse(
        ok=ok,
        translation_request_valid=translation_request_valid,
        translator_config_valid=translator_config_valid,
    )
