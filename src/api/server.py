"""FastAPI server for the OSS dashboard.

Run with:

    uvicorn src.api.server:app --host 0.0.0.0 --port 8000

This serves the HTTP+SSE surface that ``frontend/`` expects. Single-user,
single-process, in-memory state — see ``job_store.py``.

Endpoints implemented:

- POST   /jobs                                  start a scan
- GET    /jobs/{id}                             read job state
- GET    /jobs/{id}/stream                      SSE event stream
- POST   /jobs/{id}/cancel                      cancel running scan
- GET    /jobs/{id}/hypotheses                  hypothesis tree
- GET    /jobs/{id}/pentester_results           pentester findings
- GET    /jobs/{id}/recon_result                recon data
- GET    /jobs/{id}/tool_calls                  tool execution log
- GET    /jobs/{id}/reviews                     HTLI review history
- GET    /jobs/{id}/reviews/pending             pending HTLI review
- POST   /jobs/{id}/reviews/submit              submit HTLI review
- GET    /sessions/{id}                         session info (alias for /jobs)
- DELETE /sessions/{id}                         remove job
- GET    /targets, POST /targets, GET/PATCH/DELETE /targets/{id},
         POST /targets/{id}/verify              target CRUD
- GET    /credentials, POST /credentials,
         PATCH/DELETE /credentials/{id}         credential CRUD
- GET    /dashboard/stats                       aggregate stats
- GET    /dashboard/trends                      vulnerability trend
- GET    /dashboard/severity-distribution       severity buckets
- GET    /dashboard/tests                       recent scan list
- GET    /dashboard/tests/{id}                  scan detail
- GET    /dashboard/hypotheses                  all hypotheses
- GET    /dashboard/findings                    all findings
- GET    /health                                liveness probe
"""

from __future__ import annotations

import asyncio
import logging
import os
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .events import format_sse, publish, severity_summary
from .job_store import (
    CREDENTIALS,
    CredentialRecord,
    JOBS,
    Job,
    TARGETS,
    TargetRecord,
)

logger = logging.getLogger("fennec.api")
app = FastAPI(title="Fennec OSS API", version="0.1.0")

# Default to localhost-only CORS — the OSS server is designed for single-user
# local use. The regex matches http(s)://localhost or 127.0.0.1 on any port,
# so vite/preview/nginx-via-compose all work without manual port pinning.
# Override with an explicit allowlist via FENNEC_CORS_ORIGINS=a,b,c when
# proxying through a different origin. Use "*" only if you know why.
_default_localhost_regex = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"
_explicit_origins = [o.strip() for o in os.getenv("FENNEC_CORS_ORIGINS", "").split(",") if o.strip()]
if _explicit_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_explicit_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=_default_localhost_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class StartTestRequest(BaseModel):
    target_url: str
    name: Optional[str] = None
    description: Optional[str] = None
    mode: str = "black_box"
    htli: bool = False
    target_id: Optional[str] = None
    credential_id: Optional[str] = None
    method: str = "balanced"
    frequency: Optional[str] = None
    timeout_seconds: int = 600


class TargetCreate(BaseModel):
    domain: str
    name: str


class TargetUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None


class CredentialCreate(BaseModel):
    target_id: str
    name: str
    username: str
    password: str
    auth_type: str = "basic"


class CredentialUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    auth_type: Optional[str] = None


class ReviewSubmitRequest(BaseModel):
    edits: list[dict] = Field(default_factory=list)
    new_hypotheses: list[dict] = Field(default_factory=list)
    guidance_notes: str = ""


# ---------------------------------------------------------------------------
# Scan lifecycle
# ---------------------------------------------------------------------------


async def _run_job(job: Job) -> None:
    """Background task that drives a single scan to completion."""
    from agent import PentestMode, PentestTask, run_pentest

    job.mark("running")
    await publish(job, "session_start", {
        "job_id": job.id,
        "target_url": job.target_url,
        "mode": job.mode,
        "method": job.method,
    })

    # Set per-job assessment method via env (read inside run_pentest).
    # Single-process server — this is the safe place to set it.
    if job.method:
        os.environ["FENNEC_METHOD"] = job.method
    if job.credential_id:
        cred = CREDENTIALS.get(job.credential_id)
        if cred:
            import json as _json
            os.environ["FENNEC_AUTH_CREDENTIALS"] = _json.dumps({
                "username": cred.username,
                "password": cred.password,
                "auth_type": cred.auth_type,
            })

    # Bridge agent loop events into the per-job SSE stream. Each agent event
    # is fanned out to every subscriber connected to /jobs/{id}/stream. We
    # also mirror the data into the job's in-memory state so the REST GET
    # endpoints (/hypotheses, /recon_result, /pentester_results, /tool_calls)
    # return live values mid-scan, not just the final snapshot.
    async def _event_sink(event_type: str, data: dict) -> None:
        try:
            if event_type == "recon_update" and isinstance(data.get("recon_data"), dict):
                rd = data["recon_data"]
                rd.setdefault("session_id", job.id)
                rd.setdefault("target_url", job.target_url)
                job.recon_result = rd
            elif event_type == "hypothesis_tree" and isinstance(data.get("hypothesis_manager"), dict):
                tree = (data["hypothesis_manager"].get("tree") or {})
                job.hypotheses = [h for h in tree.values() if isinstance(h, dict)]
            elif event_type == "tool_call":
                job.tool_calls.append({
                    "id": data.get("tool_id") or str(len(job.tool_calls)),
                    "session_id": job.id,
                    "tool_name": data.get("tool_name", ""),
                    "tool_input": data.get("args", {}),
                    "agent": data.get("agent", ""),
                    "success": True,
                    "result": "",
                    "error": "",
                    "timestamp": data.get("timestamp", ""),
                })
            elif event_type == "tool_execution":
                # Patch the matching tool_call entry with the result.
                tid = data.get("tool_id")
                for entry in reversed(job.tool_calls):
                    if entry.get("id") == tid:
                        entry["result"] = data.get("result", "")
                        entry["success"] = bool(data.get("success", True))
                        break
            elif event_type == "hypothesis_review":
                job.pending_review = data
                job.mark("awaiting_review")
        except Exception:  # pragma: no cover — defensive
            logger.exception("event_sink mirror failed for %s", event_type)
        await publish(job, event_type, data)

    async def _await_review(interrupt_data: dict) -> dict:
        """Block the agent loop until the dashboard submits a review."""
        job.pending_review = interrupt_data
        job.mark("awaiting_review")
        edits = await job.review_queue.get()
        job.pending_review = None
        job.mark("running")
        return edits

    try:
        task = PentestTask(
            target_url=job.target_url,
            description=job.description or "Identify and exploit vulnerabilities in the target",
            mode=PentestMode(job.mode),
            timeout=job.timeout_seconds,
        )
        result = await run_pentest(
            task,
            htli=job.htli,
            event_sink=_event_sink,
            await_review=_await_review if job.htli else None,
        )
    except asyncio.CancelledError:
        job.mark("cancelled")
        await publish(job, "error", {"message": "Scan cancelled"})
        raise
    except Exception as exc:
        logger.exception("Job %s failed", job.id)
        job.error = str(exc)
        job.mark("failed")
        await publish(job, "error", {"message": str(exc)})
        return

    # run_pentest swallows its own exceptions and reports them via result.error.
    # Treat a non-empty error as a failure, regardless of whether the agent
    # also produced partial findings.
    if result.error:
        job.error = result.error
        job.mark("failed")
        await publish(job, "error", {"message": result.error})
        return

    # Populate the job with whatever the agent produced.
    job.success = result.success
    job.final_result = result.final_summary
    job.findings = [
        {
            "id": f"{job.id}-finding-{i}",
            "job_id": job.id,
            "title": vuln,
            "description": result.final_summary,
            "severity": "high",  # Pentester confirms vulnerable; severity-aware mapping is a future enhancement
            "status": "confirmed",
            "location": job.target_url,
            "parameter": "",
            "evidence": "",
            "reproduction_steps": [],
            "vulnerability_type": "",
            "cwe_id": None,
            "hypothesis_id": None,
            "discovered_at": datetime.now(timezone.utc).isoformat(),
            "discovered_by": "pentester",
        }
        for i, vuln in enumerate(result.vulnerabilities)
    ]
    # Build a pentester_results view (RichFinding shape) from execution_log.
    job.pentester_results = [
        {
            "id": i,
            "job_id": job.id,
            "hypothesis_id": None,
            "status": "completed",
            "verdict": "vulnerable",
            "evidence": [],
            "suggested_followups": [],
            "needs": [],
            "error": None,
            "description_overview": vuln,
            "owasp_category": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        for i, vuln in enumerate(result.vulnerabilities)
    ]
    # Tool calls from execution log
    job.tool_calls = [
        {
            "id": str(i),
            "session_id": job.id,
            "tool_name": entry.get("tool_name", "unknown"),
            "tool_input": entry.get("args", {}),
            "agent": entry.get("agent", "unknown"),
            "success": entry.get("status", "success") == "success",
            "result": entry.get("output", ""),
            "error": "",
            "timestamp": entry.get("timestamp", ""),
        }
        for i, entry in enumerate(result.execution_log)
        if entry.get("type") in {"tool_call", "tool_result"}
    ]
    job.mark("completed")
    await publish(job, "findings_update", {
        "findings": job.pentester_results,
        "correlations": [],
        "summary": severity_summary(job.findings),
    })
    await publish(job, "complete", {
        "success": job.success,
        "summary": job.final_result or "",
        "findings_count": len(job.findings),
    })


@app.post("/jobs")
async def create_job(req: StartTestRequest) -> dict:
    job = Job(
        id=str(uuid.uuid4()),
        name=req.name or f"Assessment – {req.target_url}",
        target_url=req.target_url,
        mode=req.mode,
        method=req.method,
        htli=req.htli,
        target_id=req.target_id,
        credential_id=req.credential_id,
        description=req.description,
        timeout_seconds=req.timeout_seconds,
        frequency=req.frequency,
    )
    JOBS.put(job)
    job.task = asyncio.create_task(_run_job(job))
    return job.to_response()


@app.get("/jobs/{job_id}")
async def get_job(job_id: str) -> dict:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_response()


@app.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str) -> dict:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.task and not job.task.done():
        job.task.cancel()
    job.mark("cancelled")
    return job.to_response()


@app.get("/jobs/{job_id}/hypotheses")
async def get_hypotheses(job_id: str) -> list[dict]:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.hypotheses


@app.get("/jobs/{job_id}/pentester_results")
async def get_pentester_results(
    job_id: str,
    exclude_safe: bool = Query(True),
) -> list[dict]:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if exclude_safe:
        return [r for r in job.pentester_results if r.get("verdict") not in {"safe", "not_vulnerable"}]
    return job.pentester_results


@app.get("/jobs/{job_id}/recon_result")
async def get_recon_result(job_id: str) -> dict:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.recon_result or {
        "session_id": job.id,
        "target_url": job.target_url,
        "recon_completed": False,
        "ports_open": [],
        "technologies": [],
        "endpoints": [],
        "entry_points": [],
        "registration_available": False,
        "headers_of_interest": [],
        "cookies_observed": [],
        "default_credentials_found": False,
        "notes": [],
    }


@app.get("/jobs/{job_id}/tool_calls")
async def get_tool_calls(job_id: str) -> list[dict]:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.tool_calls


# ---------------------------------------------------------------------------
# SSE event stream
# ---------------------------------------------------------------------------


@app.get("/jobs/{job_id}/stream")
async def stream_job(job_id: str, request: Request) -> StreamingResponse:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    queue: asyncio.Queue = asyncio.Queue(maxsize=256)
    job.subscribers.append(queue)

    async def gen() -> AsyncIterator[bytes]:
        try:
            # Replay current state on connect so late subscribers aren't stranded.
            yield format_sse("session_start", {
                "job_id": job.id,
                "target_url": job.target_url,
                "status": job.status,
            })
            if job.status in {"completed", "failed", "cancelled"}:
                yield format_sse("complete", {
                    "success": job.success,
                    "status": job.status,
                    "summary": job.final_result or "",
                })
                return

            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    # Heartbeat — keeps proxies/load-balancers from dropping us.
                    yield b": keep-alive\n\n"
                    continue
                yield format_sse(payload.get("type", "message"), payload)
                if payload.get("type") in {"complete", "error"}:
                    break
        finally:
            if queue in job.subscribers:
                job.subscribers.remove(queue)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Sessions (aliases of /jobs with a different response shape)
# ---------------------------------------------------------------------------


@app.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict:
    job = JOBS.get(session_id)
    if not job:
        raise HTTPException(status_code=404, detail="Session not found")
    return job.to_session_response()


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    job = JOBS.get(session_id)
    if not job:
        raise HTTPException(status_code=404, detail="Session not found")
    if job.task and not job.task.done():
        job.task.cancel()
    JOBS.delete(session_id)
    return {"status": "deleted", "message": f"Session {session_id} removed"}


# ---------------------------------------------------------------------------
# HTLI review endpoints
# ---------------------------------------------------------------------------


@app.get("/jobs/{job_id}/reviews")
async def list_reviews(job_id: str) -> list[dict]:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # OSS doesn't persist review history — return empty for now.
    return []


@app.get("/jobs/{job_id}/reviews/pending")
async def pending_review(job_id: str) -> dict:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "awaiting_review" or not job.pending_review:
        raise HTTPException(status_code=404, detail="No pending review")
    return {
        "id": 0,
        "job_id": job.id,
        "status": "pending",
        "hypotheses_snapshot": job.pending_review.get("hypotheses", job.hypotheses),
        "user_edits": None,
        "timeout_seconds": 600,
        "review_cycle": 1,
        "created_at": job.created_at,
        "reviewed_at": None,
        "seconds_remaining": None,
    }


@app.post("/jobs/{job_id}/reviews/submit")
async def submit_review(job_id: str, req: ReviewSubmitRequest) -> dict:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "awaiting_review":
        # Surface the submission anyway (so non-HTLI consumers can record
        # intent), but flag that the running graph won't see it.
        await publish(job, "review_submitted", {
            "edits": req.edits,
            "new_hypotheses": req.new_hypotheses,
            "guidance_notes": req.guidance_notes,
            "ignored": True,
        })
        raise HTTPException(status_code=409, detail="Job is not awaiting review")

    user_edits = {
        "edits": req.edits,
        "new_hypotheses": req.new_hypotheses,
        "guidance_notes": req.guidance_notes,
    }
    # Hand the decision to the agent loop via the per-job review queue.
    # _await_review (in _run_job) is blocked on this queue.
    try:
        job.review_queue.put_nowait(user_edits)
    except asyncio.QueueFull:
        raise HTTPException(status_code=409, detail="A review was already submitted for this interrupt")

    await publish(job, "review_submitted", user_edits)

    return {
        "id": 0,
        "job_id": job.id,
        "status": "approved",
        "hypotheses_snapshot": job.hypotheses,
        "user_edits": user_edits,
        "timeout_seconds": 600,
        "review_cycle": 1,
        "created_at": job.created_at,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "seconds_remaining": None,
    }


# ---------------------------------------------------------------------------
# Target CRUD (in-memory)
# ---------------------------------------------------------------------------


@app.get("/targets")
async def list_targets() -> list[dict]:
    return [t.to_response() for t in TARGETS.values()]


@app.post("/targets")
async def create_target(req: TargetCreate) -> dict:
    target = TargetRecord(
        id=str(uuid.uuid4()),
        domain=req.domain,
        name=req.name,
        verification_token=secrets.token_urlsafe(16),
    )
    TARGETS[target.id] = target
    return target.to_response()


@app.get("/targets/{target_id}")
async def get_target(target_id: str) -> dict:
    target = TARGETS.get(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target.to_response()


@app.patch("/targets/{target_id}")
async def update_target(target_id: str, req: TargetUpdate) -> dict:
    target = TARGETS.get(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    if req.name is not None:
        target.name = req.name
    if req.domain is not None:
        target.domain = req.domain
    target.updated_at = datetime.now(timezone.utc).isoformat()
    return target.to_response()


@app.delete("/targets/{target_id}")
async def delete_target(target_id: str) -> None:
    if target_id not in TARGETS:
        raise HTTPException(status_code=404, detail="Target not found")
    del TARGETS[target_id]


@app.post("/targets/{target_id}/verify")
async def verify_target(target_id: str) -> dict:
    target = TARGETS.get(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    # OSS: skip verification, trust the user (it's their machine).
    target.verified = True
    return {"verified": True, "message": "Target marked verified (OSS auto-trust)"}


# ---------------------------------------------------------------------------
# Credential CRUD (in-memory)
# ---------------------------------------------------------------------------


@app.get("/credentials")
async def list_credentials(target_id: Optional[str] = None) -> list[dict]:
    creds = CREDENTIALS.values()
    if target_id:
        creds = [c for c in creds if c.target_id == target_id]
    return [c.to_response() for c in creds]


@app.post("/credentials")
async def create_credential(req: CredentialCreate) -> dict:
    cred = CredentialRecord(
        id=str(uuid.uuid4()),
        target_id=req.target_id,
        name=req.name,
        username=req.username,
        password=req.password,
        auth_type=req.auth_type,
    )
    CREDENTIALS[cred.id] = cred
    return cred.to_response()


@app.patch("/credentials/{credential_id}")
async def update_credential(credential_id: str, req: CredentialUpdate) -> dict:
    cred = CREDENTIALS.get(credential_id)
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    if req.name is not None:
        cred.name = req.name
    if req.username is not None:
        cred.username = req.username
    if req.password is not None:
        cred.password = req.password
    if req.auth_type is not None:
        cred.auth_type = req.auth_type
    return cred.to_response()


@app.delete("/credentials/{credential_id}")
async def delete_credential(credential_id: str) -> None:
    if credential_id not in CREDENTIALS:
        raise HTTPException(status_code=404, detail="Credential not found")
    del CREDENTIALS[credential_id]


# ---------------------------------------------------------------------------
# Dashboard aggregations (computed from in-memory jobs)
# ---------------------------------------------------------------------------


def _aggregate_severities() -> dict[str, int]:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for job in JOBS.all():
        for f in job.findings:
            sev = (f.get("severity") or "info").lower()
            if sev in counts:
                counts[sev] += 1
    return counts


@app.get("/dashboard/stats")
async def dashboard_stats() -> dict:
    all_jobs = JOBS.all()
    sev = _aggregate_severities()
    total_vulns = sum(sev.values())
    running = sum(1 for j in all_jobs if j.status == "running")
    return {
        "total_vulnerabilities": total_vulns,
        "critical_count": sev["critical"],
        "high_count": sev["high"],
        "medium_count": sev["medium"],
        "low_count": sev["low"],
        "info_count": sev["info"],
        "risk_mitigation_value": 0,
        "issues_fixed": 0,
        "total_tests": len(all_jobs),
        "running_tests": running,
        "total_agents": 4,
        "active_agents": 4 if running else 0,
    }


@app.get("/dashboard/trends")
async def dashboard_trends(days: int = 30) -> list[dict]:
    # OSS doesn't persist enough history for a trend chart. Return an empty
    # series with the expected shape so the dashboard renders without errors.
    return []


@app.get("/dashboard/severity-distribution")
async def dashboard_severity() -> dict:
    return _aggregate_severities()


@app.get("/dashboard/tests")
async def dashboard_tests(limit: int = 20, offset: int = 0) -> list[dict]:
    jobs = JOBS.list_sorted(limit=limit, offset=offset)
    return [j.to_test_activity() for j in jobs]


@app.get("/dashboard/tests/{session_id}")
async def dashboard_test_detail(session_id: str) -> dict:
    job = JOBS.get(session_id)
    if not job:
        raise HTTPException(status_code=404, detail="Test not found")
    return job.to_test_activity()


@app.get("/dashboard/hypotheses")
async def dashboard_hypotheses(limit: int = 50) -> list[dict]:
    out: list[dict] = []
    for job in JOBS.list_sorted(limit=100, offset=0):
        out.extend(job.hypotheses)
        if len(out) >= limit:
            break
    return out[:limit]


@app.get("/dashboard/findings")
async def dashboard_findings(
    severity: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    out: list[dict] = []
    for job in JOBS.list_sorted(limit=100, offset=0):
        for f in job.findings:
            if severity and (f.get("severity") or "").lower() != severity.lower():
                continue
            out.append(f)
            if len(out) >= limit:
                return out
    return out


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "fennec-oss", "version": "0.1.0"}
