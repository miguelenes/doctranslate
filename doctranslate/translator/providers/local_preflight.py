"""Reachability and model checks for local translation backends."""

from __future__ import annotations

import json
import logging
from urllib.parse import urljoin
from urllib.parse import urlparse

import httpx

from doctranslate.translator.config import NestedTranslatorConfig
from doctranslate.translator.config import ProviderConfigModel
from doctranslate.translator.local_config import LOCAL_DEFAULT_OLLAMA_BASE
from doctranslate.translator.local_config import _make_term_provider
from doctranslate.translator.local_config import _make_translate_provider
from doctranslate.translator.local_config import _normalize_openai_compatible_base_url

logger = logging.getLogger(__name__)


class LocalPreflightError(RuntimeError):
    """Raised when a local backend is misconfigured or unreachable."""


def _ollama_host(base: str) -> str:
    b = base.rstrip("/")
    if b.endswith("/v1"):
        b = b[: -len("/v1")]
    return b


def preflight_ollama(*, base_url: str, model: str, timeout: float = 5.0) -> None:
    """Verify Ollama is up and ``model`` appears in ``GET /api/tags``."""
    host = _ollama_host(base_url or LOCAL_DEFAULT_OLLAMA_BASE)
    tags_url = urljoin(host + "/", "api/tags")
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(tags_url)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        msg = (
            f"Cannot reach Ollama at {host!r} ({e!s}). "
            "Start Ollama or set --local-base-url / local_base_url in config."
        )
        raise LocalPreflightError(msg) from e
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON from Ollama {tags_url!r}: {e!s}"
        raise LocalPreflightError(msg) from e

    models = data.get("models") if isinstance(data, dict) else None
    if not isinstance(models, list):
        msg = f"Unexpected Ollama /api/tags response shape from {tags_url!r}"
        raise LocalPreflightError(msg)

    names: set[str] = set()
    for m in models:
        if isinstance(m, dict) and m.get("name"):
            names.add(str(m["name"]))
            mod = m.get("model")
            if mod:
                names.add(str(mod))

    want = model.strip()
    if want not in names and f"{want}:latest" not in names:
        short = sorted(n for n in names if want.split(":")[0] in n)[:8]
        hint = f" Similar tags: {short}" if short else ""
        msg = (
            f"Ollama model {want!r} not found locally (under {host}). "
            f"Run: ollama pull {want.split(':')[0]}{hint}"
        )
        raise LocalPreflightError(msg)


def _openai_models_url(base_url: str) -> str:
    u = _normalize_openai_compatible_base_url(base_url)
    parsed = urlparse(u)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    return urljoin(origin + "/", "v1/models")


def preflight_openai_compatible(
    *,
    base_url: str,
    model: str,
    api_key: str | None,
    timeout: float = 5.0,
) -> None:
    """Verify an OpenAI-compatible server lists ``model`` (best-effort)."""
    models_url = _openai_models_url(base_url)
    headers: dict[str, str] = {}
    key = (api_key or "").strip()
    if key and key != "EMPTY":
        headers["Authorization"] = f"Bearer {key}"

    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(models_url, headers=headers)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        msg = (
            f"Cannot reach OpenAI-compatible server at {models_url!r} ({e!s}). "
            "Check --local-base-url and that the server is running."
        )
        raise LocalPreflightError(msg) from e
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON from {models_url!r}: {e!s}"
        raise LocalPreflightError(msg) from e

    found = False
    if isinstance(data, dict) and "data" in data:
        for item in data.get("data") or []:
            if isinstance(item, dict) and item.get("id") == model:
                found = True
                break
    if not found:
        logger.warning(
            "Could not confirm model %r in GET %s (server may use a different listing shape).",
            model,
            models_url,
        )


def run_local_preflight(nested: NestedTranslatorConfig) -> None:
    """Run checks for the translate + term providers implied by local nested config."""
    if nested.translator != "local":
        return
    t_cfg = _make_translate_provider(nested)
    term_cfg = _make_term_provider(nested)
    _preflight_provider(t_cfg)
    if term_cfg.model != t_cfg.model or term_cfg.base_url != t_cfg.base_url or term_cfg.provider != t_cfg.provider:
        _preflight_provider(term_cfg)


def _preflight_provider(cfg: ProviderConfigModel) -> None:
    timeout = min(15.0, max(2.0, float(cfg.timeout_seconds)))
    if cfg.provider == "ollama":
        preflight_ollama(base_url=cfg.base_url or LOCAL_DEFAULT_OLLAMA_BASE, model=cfg.model, timeout=timeout)
        return
    if cfg.provider == "openai_compatible":
        if not cfg.base_url:
            msg = "local_base_url is required for OpenAI-compatible local backends"
            raise LocalPreflightError(msg)
        preflight_openai_compatible(
            base_url=cfg.base_url,
            model=cfg.model,
            api_key=cfg.api_key,
            timeout=timeout,
        )
        return
    msg = f"Unsupported provider for local preflight: {cfg.provider!r}"
    raise LocalPreflightError(msg)
