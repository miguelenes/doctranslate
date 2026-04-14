"""Build :class:`arq.connections.RedisSettings` from a Redis URL."""

from __future__ import annotations

from urllib.parse import unquote
from urllib.parse import urlparse

from arq.connections import RedisSettings


def redis_settings_from_url(url: str) -> RedisSettings:
    """Parse ``redis://`` or ``rediss://`` URLs into ARQ :class:`RedisSettings`."""
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = int(parsed.port or 6379)
    db = 0
    if parsed.path and len(parsed.path) > 1:
        db = int(parsed.path.lstrip("/").split("/")[0] or "0")
    password = unquote(parsed.password) if parsed.password else None
    ssl = parsed.scheme == "rediss"
    return RedisSettings(
        host=host,
        port=port,
        database=db,
        password=password,
        ssl=ssl,
    )
