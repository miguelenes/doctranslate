"""Container-oriented HTTP API for DocTranslater (optional ``DocTranslater[api]``)."""

from __future__ import annotations

__all__ = ["create_app"]


def __getattr__(name: str) -> object:
    if name == "create_app":
        from doctranslate.http_api.app import create_app

        return create_app
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
