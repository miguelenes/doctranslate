"""Shared-secret authentication for the OSS HTTP API (Bearer or API key header)."""

from __future__ import annotations

import secrets
from collections.abc import Awaitable
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.responses import Response

from doctranslate.http_api.errors import http_error
from doctranslate.http_api.settings import ApiSettings
from doctranslate.http_api.settings import get_settings
from doctranslate.observability.context import get_request_id
from doctranslate.schemas.enums import PublicErrorCode
from doctranslate.schemas.public_api import TranslationErrorPayload


def read_bearer_credentials(request: Request) -> HTTPAuthorizationCredentials | None:
    """Parse ``Authorization: Bearer …`` without registering an OpenAPI security dependency."""
    auth = request.headers.get("Authorization")
    if not auth:
        return None
    parts = auth.split(None, 1)
    if len(parts) != 2:
        return None
    scheme, credentials = parts[0].strip(), parts[1].strip()
    if scheme.lower() != "bearer" or not credentials:
        return None
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=credentials)


def _expected_secret(settings: ApiSettings) -> str | None:
    if settings.auth_token is None:
        return None
    return settings.auth_token.get_secret_value()


def _presented_token(
    request: Request,
    settings: ApiSettings,
    bearer: HTTPAuthorizationCredentials | None,
) -> str | None:
    if bearer is not None and bearer.scheme.lower() == "bearer" and bearer.credentials:
        return bearer.credentials.strip()
    name = settings.auth_header_api_key_name
    raw = request.headers.get(name)
    if raw is not None and raw.strip():
        return raw.strip()
    return None


def _token_valid(settings: ApiSettings, presented: str | None) -> bool:
    expected = _expected_secret(settings)
    if expected is None or not expected:
        return False
    if presented is None:
        return False
    return secrets.compare_digest(presented.encode("utf-8"), expected.encode("utf-8"))


def _auth_401(request_id: str | None, *, api_key_header_name: str) -> HTTPException:
    return http_error(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error=TranslationErrorPayload(
            code=PublicErrorCode.VALIDATION_ERROR,
            message=(
                "Authentication required. Send "
                "`Authorization: Bearer <token>` or "
                f"`{api_key_header_name}: <token>`."
            ),
            retryable=False,
        ),
        request_id=request_id,
    )


def _auth_401_invalid(request_id: str | None) -> HTTPException:
    return http_error(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error=TranslationErrorPayload(
            code=PublicErrorCode.VALIDATION_ERROR,
            message="Invalid authentication credentials.",
            retryable=False,
        ),
        request_id=request_id,
    )


def _ensure_operator_credentials(
    *,
    settings: ApiSettings,
    request: Request,
    bearer: HTTPAuthorizationCredentials | None,
) -> None:
    presented = _presented_token(request, settings, bearer)
    rid = get_request_id()
    if presented is None:
        raise _auth_401(rid, api_key_header_name=settings.auth_header_api_key_name)
    if not _token_valid(settings, presented):
        raise _auth_401_invalid(rid)


async def require_api_operator(
    request: Request,
    settings: Annotated[ApiSettings, Depends(get_settings)],
) -> None:
    """Require a valid Bearer token or API key when ``auth_mode`` is ``required``."""
    if settings.auth_mode == "disabled":
        return
    bearer = read_bearer_credentials(request)
    _ensure_operator_credentials(settings=settings, request=request, bearer=bearer)


async def require_api_operator_when_probes_are_protected(
    request: Request,
    settings: Annotated[ApiSettings, Depends(get_settings)],
) -> None:
    """For ``/v1/health/live`` and ``/v1/health/ready`` only: auth when probes are not public."""
    if settings.auth_mode == "disabled":
        return
    if settings.auth_allow_unauthenticated_probe_paths:
        return
    bearer = read_bearer_credentials(request)
    _ensure_operator_credentials(settings=settings, request=request, bearer=bearer)


def operator_auth_paths(settings: ApiSettings) -> frozenset[str]:
    """Paths protected by :class:`OperatorPathsAuthMiddleware` (metrics + optional OpenAPI)."""
    from doctranslate.observability.config import get_observability_settings

    obs = get_observability_settings()
    mp = obs.metrics_path.strip() or "/metrics"
    if not mp.startswith("/"):
        mp = "/" + mp
    paths = {mp}
    if settings.docs_enabled:
        paths.update({"/docs", "/openapi.json", "/redoc"})
    return frozenset(paths)


class OperatorPathsAuthMiddleware(BaseHTTPMiddleware):
    """ASGI middleware: enforce operator auth on mounted metrics and OpenAPI routes."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        settings = get_settings()
        if settings.auth_mode == "disabled":
            return await call_next(request)
        path = request.url.path
        if path not in operator_auth_paths(settings):
            return await call_next(request)
        bearer = read_bearer_credentials(request)
        presented = _presented_token(request, settings, bearer)
        rid = get_request_id()
        if presented is None:
            exc = _auth_401(rid, api_key_header_name=settings.auth_header_api_key_name)
        elif not _token_valid(settings, presented):
            exc = _auth_401_invalid(rid)
        else:
            return await call_next(request)
        detail = exc.detail
        if isinstance(detail, dict):
            return JSONResponse(status_code=exc.status_code, content=detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": str(detail)},
        )


def apply_openapi_http_api_auth(schema: dict, settings: ApiSettings) -> dict:
    """When auth is required, document Bearer or API key (OR) on operations; public probes get ``security: []``."""
    if settings.auth_mode != "required":
        return schema
    components = schema.setdefault("components", {})
    schemes = components.setdefault("securitySchemes", {})
    schemes["HTTPBearer"] = {
        "type": "http",
        "scheme": "bearer",
        "description": "Shared secret (opaque token), not a JWT.",
    }
    schemes["ApiKeyAuth"] = {
        "type": "apiKey",
        "in": "header",
        "name": settings.auth_header_api_key_name,
    }
    or_block = [{"HTTPBearer": []}, {"ApiKeyAuth": []}]
    probe_public = settings.auth_allow_unauthenticated_probe_paths
    for path_key, path_item in schema.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue
            m = method.lower()
            if m not in {"get", "post", "put", "patch", "delete", "head", "options"}:
                continue
            if (
                probe_public
                and m == "get"
                and path_key in {"/v1/health/live", "/v1/health/ready"}
            ):
                operation["security"] = []
            else:
                operation["security"] = or_block
    return schema


def install_openapi_auth_extension(app: FastAPI) -> None:
    """Replace ``app.openapi`` to merge auth documentation when ``auth_mode=required``."""

    def custom_openapi() -> dict:
        if app.openapi_schema is not None:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=str(app.version),
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
        )
        openapi_schema = apply_openapi_http_api_auth(openapi_schema, get_settings())
        app.openapi_schema = openapi_schema
        return openapi_schema

    app.openapi = custom_openapi  # type: ignore[method-assign]
