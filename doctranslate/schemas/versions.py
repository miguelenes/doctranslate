"""Version constants for the stable public schema contract."""

from __future__ import annotations

# Bump on breaking changes to public Pydantic models or progress event wire format.
PUBLIC_SCHEMA_VERSION = "1"

# Progress / callback envelope revision (subset of schema for streaming events).
PROGRESS_EVENT_VERSION = "1"
