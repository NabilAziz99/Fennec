"""In-memory job state for the OSS dashboard backend.

Jobs are keyed by UUID. Each job carries its inputs, current status,
the streaming event log, and the final agent outputs (recon, hypotheses,
pentester results) as they're produced.

No persistence across server restarts — by design. The paid SaaS uses
Postgres; the OSS distribution is single-user and ephemeral.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Job:
    id: str
    name: str
    target_url: str
    mode: str = "black_box"
    method: str = "balanced"
    htli: bool = False
    target_id: Optional[str] = None
    credential_id: Optional[str] = None
    description: Optional[str] = None
    timeout_seconds: int = 600
    frequency: Optional[str] = None
    scheduled_at: Optional[str] = None

    status: str = "queued"  # queued | running | completed | failed | cancelled | awaiting_review
    created_at: str = field(default_factory=_now)
    updated_at: Optional[str] = None

    # Live outputs populated as the scan runs
    recon_result: Optional[dict] = None
    hypotheses: list[dict] = field(default_factory=list)
    pentester_results: list[dict] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    findings: list[dict] = field(default_factory=list)

    # Final outcome
    success: bool = False
    final_result: Optional[str] = None
    error: Optional[str] = None

    # Bookkeeping for background task and SSE subscribers
    task: Optional[asyncio.Task] = field(default=None, repr=False)
    subscribers: list[asyncio.Queue] = field(default_factory=list, repr=False)

    def to_response(self) -> dict:
        """JobResponse shape expected by frontend types."""
        return {
            "id": self.id,
            "user_id": "local",
            "name": self.name,
            "status": self.status,
            "target_url": self.target_url,
            "mode": self.mode,
            "timeout_seconds": self.timeout_seconds,
            "description": self.description,
            "htli": self.htli,
            "target_id": self.target_id,
            "credential_id": self.credential_id,
            "method": self.method,
            "frequency": self.frequency,
            "scheduled_at": self.scheduled_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_session_response(self) -> dict:
        return {
            "session_id": self.id,
            "status": self.status,
            "target_url": self.target_url,
        }

    def to_test_activity(self) -> dict:
        """TestActivity shape — used by /dashboard/tests."""
        sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in self.findings:
            s = (f.get("severity") or "info").lower()
            if s in sev:
                sev[s] += 1
        duration = "—"
        if self.updated_at and self.created_at:
            try:
                start = datetime.fromisoformat(self.created_at)
                end = datetime.fromisoformat(self.updated_at)
                secs = int((end - start).total_seconds())
                duration = f"{secs // 60}m {secs % 60}s" if secs >= 60 else f"{secs}s"
            except Exception:
                pass
        return {
            "id": self.id,
            "title": self.name,
            "status": self.status if self.status in {
                "completed", "running", "pending", "failed", "awaiting_review",
            } else "completed",
            "target_url": self.target_url,
            "issues": sev,
            "duration": duration,
            "started_at": self.created_at,
            "completed_at": self.updated_at if self.status in {"completed", "failed", "cancelled"} else None,
            "hypothesis_count": len(self.hypotheses),
            "findings_count": len(self.findings),
            "method": self.method,
            "credential_id": self.credential_id,
            "initiated_by": "local",
        }

    def mark(self, status: str) -> None:
        self.status = status
        self.updated_at = _now()


class JobStore:
    """Process-local job store. Single-user, no locking beyond asyncio."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def put(self, job: Job) -> None:
        self._jobs[job.id] = job

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def delete(self, job_id: str) -> bool:
        return self._jobs.pop(job_id, None) is not None

    def all(self) -> list[Job]:
        return list(self._jobs.values())

    def list_sorted(self, limit: int = 20, offset: int = 0) -> list[Job]:
        jobs = sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)
        return jobs[offset : offset + limit]


# Module-level singleton — one server, one store.
JOBS = JobStore()


@dataclass
class TargetRecord:
    id: str
    domain: str
    name: str
    verified: bool = False
    verification_token: Optional[str] = None
    last_scanned: Optional[str] = None
    created_at: str = field(default_factory=_now)
    updated_at: Optional[str] = None

    def to_response(self, severity_counts: Optional[dict] = None) -> dict:
        return {
            "id": self.id,
            "user_id": "local",
            "domain": self.domain,
            "name": self.name,
            "verified": self.verified,
            "verification_token": self.verification_token,
            "severity_counts": severity_counts or {},
            "last_scanned": self.last_scanned,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class CredentialRecord:
    id: str
    target_id: str
    name: str
    username: str
    password: str  # not returned in responses
    auth_type: str = "basic"
    created_at: str = field(default_factory=_now)

    def to_response(self) -> dict:
        return {
            "id": self.id,
            "target_id": self.target_id,
            "name": self.name,
            "username": self.username,
            "auth_type": self.auth_type,
            "created_at": self.created_at,
        }


TARGETS: dict[str, TargetRecord] = {}
CREDENTIALS: dict[str, CredentialRecord] = {}
