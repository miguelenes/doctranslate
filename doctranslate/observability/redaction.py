"""Redact secrets and sensitive fields from log event dicts."""

from __future__ import annotations

import re
from typing import Any

_REDACT_KEYS = frozenset(
    {
        "authorization",
        "api_key",
        "apikey",
        "password",
        "secret",
        "token",
        "openai_api_key",
        "x-api-key",
        "bearer",
    },
)

# Signed URL query params often contain signatures
_URL_SECRET_PARAMS = re.compile(
    r"([?&])(X-Amz-Credential|X-Amz-Signature|signature|token|key)=[^&]*",
    re.IGNORECASE,
)


def redact_string(value: str, *, redact_user_text: bool) -> str:
    """Redact known secret patterns from a string."""
    if not value:
        return value
    s = _URL_SECRET_PARAMS.sub(r"\1\2=<redacted>", value)
    if redact_user_text and len(s) > 512:
        return s[:256] + "…<truncated>…" + s[-128:]
    return s


def redact_value(obj: Any, *, redact_user_text: bool) -> Any:
    """Recursively redact dict/list structures."""
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            lk = str(k).lower().replace("-", "_")
            if lk in _REDACT_KEYS or "secret" in lk or "password" in lk or "token" in lk:
                out[k] = "<redacted>"
            else:
                out[k] = redact_value(v, redact_user_text=redact_user_text)
        return out
    if isinstance(obj, list):
        return [redact_value(x, redact_user_text=redact_user_text) for x in obj]
    if isinstance(obj, str):
        return redact_string(obj, redact_user_text=redact_user_text)
    return obj
