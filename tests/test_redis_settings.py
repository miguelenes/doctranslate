"""Redis URL parsing for ARQ."""

from __future__ import annotations

from doctranslate.http_api.redis_settings import redis_settings_from_url


def test_redis_settings_default_localhost() -> None:
    s = redis_settings_from_url("redis://127.0.0.1:6379/0")
    assert s.host == "127.0.0.1"
    assert s.port == 6379
    assert s.database == 0
    assert s.ssl is False


def test_redis_settings_password_and_db() -> None:
    token = "x-test-redis-auth-token"
    s = redis_settings_from_url(f"redis://:{token}@example.com:6380/2")
    assert s.host == "example.com"
    assert s.port == 6380
    assert s.database == 2
    assert s.password == token
