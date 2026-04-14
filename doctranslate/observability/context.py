"""Context variables for request/job correlation."""

from __future__ import annotations

import contextvars
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "doctranslate_request_id",
    default=None,
)
_job_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "doctranslate_job_id",
    default=None,
)
_job_kind: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "doctranslate_job_kind",
    default=None,
)
_cli_run_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "doctranslate_cli_run_id",
    default=None,
)


def get_request_id() -> str | None:
    return _request_id.get()


def set_request_id(value: str | None) -> contextvars.Token[str | None]:
    return _request_id.set(value)


def reset_request_id(token: contextvars.Token[str | None]) -> None:
    _request_id.reset(token)


def new_request_id() -> str:
    return str(uuid.uuid4())


def get_job_id() -> str | None:
    return _job_id.get()


def set_job_id(value: str | None) -> contextvars.Token[str | None]:
    return _job_id.set(value)


def reset_job_id(token: contextvars.Token[str | None]) -> None:
    _job_id.reset(token)


def get_job_kind() -> str | None:
    return _job_kind.get()


def set_job_kind(value: str | None) -> contextvars.Token[str | None]:
    return _job_kind.set(value)


def reset_job_kind(token: contextvars.Token[str | None]) -> None:
    _job_kind.reset(token)


def get_cli_run_id() -> str | None:
    return _cli_run_id.get()


def set_cli_run_id(value: str | None) -> contextvars.Token[str | None]:
    return _cli_run_id.set(value)


def reset_cli_run_id(token: contextvars.Token[str | None]) -> None:
    _cli_run_id.reset(token)


def new_cli_run_id() -> str:
    return str(uuid.uuid4())


@contextmanager
def bound_observability_context(
    *,
    request_id: str | None = None,
    job_id: str | None = None,
    job_kind: str | None = None,
) -> Iterator[None]:
    """Bind correlation ids for the duration of the context manager."""
    tokens: list[tuple[contextvars.ContextVar[Any], contextvars.Token[Any]]] = []
    try:
        if request_id is not None:
            tokens.append((_request_id, _request_id.set(request_id)))
        if job_id is not None:
            tokens.append((_job_id, _job_id.set(job_id)))
        if job_kind is not None:
            tokens.append((_job_kind, _job_kind.set(job_kind)))
        yield
    finally:
        for var, tok in reversed(tokens):
            var.reset(tok)
