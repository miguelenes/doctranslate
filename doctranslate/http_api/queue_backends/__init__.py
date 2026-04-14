"""Pluggable job queue backends for the HTTP API."""

from __future__ import annotations

from doctranslate.http_api.queue_backends.base import QueueBackend

__all__ = ["QueueBackend"]
