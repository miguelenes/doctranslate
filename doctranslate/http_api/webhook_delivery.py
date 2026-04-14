"""Outbound job webhooks (compact terminal payload + retries)."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import ipaddress
import json
import logging
import os
import secrets
import time
import uuid
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from doctranslate.http_api.metadata_store.sqlite import SqliteJobMetadataStore
from doctranslate.http_api.settings import ApiSettings
from doctranslate.schemas.versions import PUBLIC_SCHEMA_VERSION

logger = logging.getLogger(__name__)

_TERMINAL = frozenset({"succeeded", "failed", "canceled"})


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _webhook_secret(cfg: dict[str, Any]) -> str | None:
    env_key = cfg.get("secret_env")
    if isinstance(env_key, str) and env_key.strip():
        return os.environ.get(env_key.strip())
    sec = cfg.get("secret")
    if isinstance(sec, str) and sec:
        return sec
    return None


def validate_webhook_url(url: str, *, settings: ApiSettings) -> None:
    """Raise ValueError when the callback URL is not allowed."""
    if not url or len(url) > 2048:
        msg = "webhook url invalid"
        raise ValueError(msg)
    p = urlparse(url)
    if p.scheme not in ("https", "http"):
        msg = "webhook url must be http(s)"
        raise ValueError(msg)
    if settings.webhook_https_required and p.scheme != "https":
        msg = "webhook url must use https"
        raise ValueError(msg)
    host = p.hostname
    if not host:
        msg = "webhook url missing host"
        raise ValueError(msg)
    if host in {"localhost"} or host.endswith(".local"):
        msg = "webhook host not allowed"
        raise ValueError(msg)
    try:
        infos = ipaddress.ip_address(host)
        if (
            infos.is_private
            or infos.is_loopback
            or infos.is_link_local
            or infos.is_multicast
            or infos.is_reserved
        ):
            msg = "webhook host not allowed"
            raise ValueError(msg)
    except ValueError:
        pass
    allow = settings.webhook_allow_hosts
    if allow:
        if host not in allow and not any(
            host == h or host.endswith(f".{h}") for h in allow
        ):
            msg = "webhook host not in allowlist"
            raise ValueError(msg)


def sign_standard_webhook_v1(*, secret: str, msg_id: str, ts: int, body: bytes) -> str:
    """Return ``webhook-signature`` header value (``v1,<base64>``)."""
    to_sign = f"{msg_id}.{ts}.".encode() + body
    mac = hmac.new(
        secret.encode(),
        to_sign,
        hashlib.sha256,
    ).digest()
    return "v1," + base64.b64encode(mac).decode("ascii")


def build_terminal_payload(
    *,
    job_id: str,
    raw: dict[str, Any],
    public_base: str,
) -> dict[str, Any]:
    state = str(raw.get("state", ""))
    err = raw.get("error")
    return {
        "type": "job.terminal",
        "schema_version": PUBLIC_SCHEMA_VERSION,
        "job_id": job_id,
        "kind": raw.get("kind"),
        "state": state,
        "seq": int(raw.get("progress_seq") or 0),
        "result_url": f"{public_base}/v1/jobs/{job_id}/result",
        "manifest_url": f"{public_base}/v1/jobs/{job_id}/manifest",
        "error": err,
    }


def maybe_enqueue_terminal_webhook(
    metadata_store: SqliteJobMetadataStore,
    *,
    job_id: str,
) -> None:
    from doctranslate.http_api.settings import get_settings

    settings = get_settings()
    public_base = (settings.public_base_url or "").rstrip("/")
    raw = metadata_store.get_job_raw(job_id)
    if raw is None:
        return
    state = str(raw.get("state", ""))
    if state not in _TERMINAL:
        return
    wh = raw.get("webhook_json")
    if not wh or not isinstance(wh, str):
        return
    try:
        cfg = json.loads(wh)
    except json.JSONDecodeError:
        logger.warning("Invalid webhook_json for job %s", job_id)
        return
    url = cfg.get("url")
    if not isinstance(url, str) or not url:
        return
    payload = build_terminal_payload(job_id=job_id, raw=raw, public_base=public_base)
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    delivery_id = f"{job_id}:terminal"
    metadata_store.enqueue_webhook_delivery(
        delivery_id=delivery_id,
        job_id=job_id,
        payload_json=json.dumps(
            {
                "url": url,
                "webhook_cfg": cfg,
                "body_b64": base64.b64encode(body).decode("ascii"),
            },
            separators=(",", ":"),
        ),
        next_attempt_at_iso=_utc_iso_now(),
    )


def _next_backoff_seconds(attempt: int) -> float:
    base = min(900.0, 2.0 ** min(attempt, 10))
    return base * (0.5 + secrets.SystemRandom().random())


async def run_webhook_delivery_sweep(
    *,
    metadata_store: SqliteJobMetadataStore,
    settings: ApiSettings,
) -> None:
    now = _utc_iso_now()
    rows = metadata_store.claim_webhook_due(
        limit=settings.webhook_delivery_batch, now_iso=now
    )
    for row in rows:
        await _deliver_one(metadata_store, settings=settings, row=row)


async def _deliver_one(
    metadata_store: SqliteJobMetadataStore,
    *,
    settings: ApiSettings,
    row: dict[str, Any],
) -> None:
    delivery_id = row["delivery_id"]
    job_id = row["job_id"]
    attempt = int(row["attempt_count"])
    try:
        outer = json.loads(row["payload_json"])
        url = str(outer["url"])
        cfg = outer["webhook_cfg"]
        body = base64.b64decode(str(outer["body_b64"]))
    except Exception as exc:
        logger.warning("Bad webhook payload %s: %s", delivery_id, exc)
        metadata_store.delete_webhook_delivery(delivery_id)
        return
    secret = _webhook_secret(cfg)
    if not secret:
        logger.warning("Missing webhook secret for delivery %s", delivery_id)
        metadata_store.delete_webhook_delivery(delivery_id)
        return
    msg_id = str(uuid.uuid4())
    ts = int(time.time())
    sig = sign_standard_webhook_v1(secret=secret, msg_id=msg_id, ts=ts, body=body)
    headers = {
        "Content-Type": "application/json",
        "webhook-id": msg_id,
        "webhook-timestamp": str(ts),
        "webhook-signature": sig,
        "User-Agent": "DocTranslater-Webhook/1",
    }
    timeout = httpx.Timeout(settings.webhook_http_timeout_seconds)
    try:
        resp = await asyncio_to_thread_httpx_post(
            url, body=body, headers=headers, timeout=timeout
        )
    except Exception as exc:
        _schedule_retry(
            metadata_store,
            delivery_id=delivery_id,
            attempt=attempt,
            err=str(exc),
            http_status=None,
            settings=settings,
        )
        return
    if 200 <= resp.status_code < 300:
        metadata_store.delete_webhook_delivery(delivery_id)
        return
    if resp.status_code in {410, 404}:
        metadata_store.delete_webhook_delivery(delivery_id)
        return
    _schedule_retry(
        metadata_store,
        delivery_id=delivery_id,
        attempt=attempt,
        err=resp.text[:512],
        http_status=resp.status_code,
        settings=settings,
    )


def _schedule_retry(
    metadata_store: SqliteJobMetadataStore,
    *,
    delivery_id: str,
    attempt: int,
    err: str,
    http_status: int | None,
    settings: ApiSettings,
) -> None:
    nxt = attempt + 1
    if nxt >= settings.webhook_max_attempts:
        logger.warning(
            "Webhook delivery %s abandoned after %s attempts (%s)",
            delivery_id,
            nxt,
            err,
        )
        metadata_store.delete_webhook_delivery(delivery_id)
        return
    delay = _next_backoff_seconds(nxt)
    when = (datetime.now(timezone.utc) + timedelta(seconds=delay)).isoformat()
    metadata_store.mark_webhook_attempt(
        delivery_id=delivery_id,
        attempt_count=nxt,
        next_attempt_at_iso=when,
        last_http_status=http_status,
        last_error=err[:2000],
    )


async def asyncio_to_thread_httpx_post(
    url: str,
    *,
    body: bytes,
    headers: dict[str, str],
    timeout: httpx.Timeout,
) -> httpx.Response:
    def _run() -> httpx.Response:
        with httpx.Client(timeout=timeout) as client:
            return client.post(url, content=body, headers=headers)

    return await asyncio.to_thread(_run)
