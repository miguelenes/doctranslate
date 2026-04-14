"""HTTP API Pydantic models."""

from __future__ import annotations

import pytest
from doctranslate.http_api.models import ConfigValidateRequest
from pydantic import ValidationError


def test_config_validate_request_requires_payload() -> None:
    with pytest.raises(ValidationError):
        ConfigValidateRequest.model_validate({})
