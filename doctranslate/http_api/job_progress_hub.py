"""In-process fan-out for live job progress (translation jobs on this API replica)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class JobProgressHub:
    """Broadcast progress dicts to SSE subscribers for one replica (in-process jobs)."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._subscribers: dict[str, set[asyncio.Queue[Any]]] = {}

    def notify(self, job_id: str, seq: int, event: dict[str, Any]) -> None:
        """Fan-out to subscribers (best-effort; never raises)."""
        payload = {"seq": int(seq), "event": dict(event)}
        subs = self._subscribers.get(job_id)
        if not subs:
            return
        for q in list(subs):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                logger.debug("Progress fan-out queue full for job %s", job_id)

    async def subscribe(self, job_id: str) -> asyncio.Queue[Any]:
        q: asyncio.Queue[Any] = asyncio.Queue(maxsize=256)
        async with self._lock:
            self._subscribers.setdefault(job_id, set()).add(q)
        return q

    async def unsubscribe(self, job_id: str, q: asyncio.Queue[Any]) -> None:
        async with self._lock:
            subs = self._subscribers.get(job_id)
            if not subs:
                return
            subs.discard(q)
            if not subs:
                self._subscribers.pop(job_id, None)
