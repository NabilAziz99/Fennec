"""SSE event publishing for the OSS server.

Each running job has a list of subscriber asyncio.Queues (the open SSE
connections). publish_event pushes a typed event onto every subscriber's
queue. The /jobs/{id}/stream endpoint consumes from its own queue and
formats the SSE wire protocol.

The event types here are a subset of what the paid version emits — enough
for the dashboard's primary flows (start scan, watch progress, see
findings + recon as they land). Richer per-tool / per-step events can be
added later without a wire-protocol break.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from .job_store import Job


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def publish(job: Job, event_type: str, data: dict[str, Any]) -> None:
    """Fan out a single event to every SSE subscriber of this job.

    Subscribers with full queues drop events rather than blocking the
    publisher — the dashboard tolerates gaps better than it tolerates
    deadlocks.
    """
    payload = {"type": event_type, **data, "session_id": job.id, "timestamp": _now()}
    dead: list[asyncio.Queue] = []
    for q in job.subscribers:
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        if q in job.subscribers:
            job.subscribers.remove(q)


def format_sse(event_type: str, data: dict[str, Any]) -> bytes:
    """Render one SSE frame (event: ... / data: JSON / blank line)."""
    body = json.dumps(data, default=str)
    return f"event: {event_type}\ndata: {body}\n\n".encode("utf-8")


def severity_summary(findings: list[dict]) -> dict[str, int]:
    summary = {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        sev = (f.get("severity") or "info").lower()
        summary["total"] += 1
        if sev in summary:
            summary[sev] += 1
    return summary
