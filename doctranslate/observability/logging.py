"""Structured logging setup (structlog + stdlib integration)."""

from __future__ import annotations

import logging
import sys
from typing import Any

from doctranslate.observability.config import ObservabilitySettings
from doctranslate.observability.context import get_cli_run_id
from doctranslate.observability.context import get_job_id
from doctranslate.observability.context import get_job_kind
from doctranslate.observability.context import get_request_id
from doctranslate.observability.redaction import redact_value

_CONFIGURED = False


def _add_obs_context(
    _logger: Any,
    _method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    if get_request_id():
        event_dict.setdefault("request_id", get_request_id())
    if get_job_id():
        event_dict.setdefault("job_id", get_job_id())
    if get_job_kind():
        event_dict.setdefault("job_kind", get_job_kind())
    if get_cli_run_id():
        event_dict.setdefault("cli_run_id", get_cli_run_id())
    event_dict.setdefault("service", "doctranslate")
    return event_dict


def _redact_processor(settings: ObservabilitySettings):
    def processor(
        _logger: Any,
        _method_name: str,
        event_dict: dict[str, Any],
    ) -> dict[str, Any]:
        if not settings.redact_user_text:
            return event_dict
        for key in ("details", "error", "message", "event"):
            if key in event_dict and isinstance(event_dict[key], (dict, list, str)):
                event_dict[key] = redact_value(
                    event_dict[key],
                    redact_user_text=settings.redact_user_text,
                )
        return event_dict

    return processor


def configure_logging(settings: ObservabilitySettings | None = None) -> None:
    """Idempotent: configure structlog + root logging level."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    if settings is None:
        from doctranslate.observability.config import get_observability_settings

        settings = get_observability_settings()

    level = getattr(logging, settings.log_level, logging.INFO)
    logging.getLogger().setLevel(level)

    try:
        import structlog
    except ImportError:
        _CONFIGURED = True
        return

    shared = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _add_obs_context,
        _redact_processor(settings),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.log_format == "json":
        processors = shared + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = shared + [
            structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty()),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    _CONFIGURED = True


def get_structlog():
    """Return structlog module or None if not installed."""
    try:
        import structlog

        return structlog
    except ImportError:
        return None


def log_event(
    name: str,
    event: str,
    *,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    """Log a structured event using structlog if available, else stdlib."""
    configure_logging()
    sl = get_structlog()
    if sl is not None:
        log = sl.get_logger(name)
        log.log(level, event, **fields)
        return
    log = logging.getLogger(name)
    extra = {"event": event, **fields}
    log.log(level, "%s %s", event, extra)
