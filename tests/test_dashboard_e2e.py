"""
End-to-end dashboard test for Fennec AI.

Tests the full flow:
1. Dashboard data store functions (register/query)
2. Dashboard REST API endpoints via FastAPI TestClient
3. Full SSE stream → dashboard sync (with OpenRouter LLM + Docker)

Usage:
    # Unit + API tests only (no Docker/LLM needed):
    pytest tests/test_dashboard_e2e.py -k "not live" -v

    # Full E2E (needs Docker running + OpenRouter key):
    pytest tests/test_dashboard_e2e.py -v
"""

import os
import sys
import json
import asyncio
import pytest

# Add project root to path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from httpx import AsyncClient, ASGITransport
import importlib.util

# Import dashboard module directly from file path (avoids src/api/__init__.py
# which transitively imports graph → agents → langchain, breaking collection).
# We also block `src.api` from being resolved as a package import.
_dashboard_path = os.path.join(project_dir, "src", "api", "dashboard.py")
_spec = importlib.util.spec_from_file_location(
    "_isolated_dashboard", _dashboard_path,
    submodule_search_locations=[],
)
dashboard = importlib.util.module_from_spec(_spec)
sys.modules["_isolated_dashboard"] = dashboard
_spec.loader.exec_module(dashboard)

_test_sessions = dashboard._test_sessions
_hypotheses = dashboard._hypotheses
_findings = dashboard._findings
register_test_session = dashboard.register_test_session
register_hypothesis = dashboard.register_hypothesis
register_finding = dashboard.register_finding
complete_test_session = dashboard.complete_test_session


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_stores():
    """Clear in-memory stores before each test."""
    _test_sessions.clear()
    _hypotheses.clear()
    _findings.clear()
    yield
    _test_sessions.clear()
    _hypotheses.clear()
    _findings.clear()


@pytest.fixture
def app():
    """Create a FastAPI app instance (lazy import to avoid graph compilation)."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    # Build a minimal app with just the dashboard router for unit/API tests
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
    )
    app.include_router(dashboard.router)

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app


@pytest.fixture
def seed_session():
    """Seed a test session with hypotheses and findings."""
    sid = "test-session-001"
    register_test_session(sid, "http://target.local:9000")

    register_hypothesis(
        hypothesis_id="hyp-001",
        session_id=sid,
        title="Test SQL Injection on /login",
        description="Check username param for SQLi",
        status="completed",
        result="vulnerable",
        severity="critical",
        required_agent="pentester",
    )
    register_hypothesis(
        hypothesis_id="hyp-002",
        session_id=sid,
        title="Check XSS on /search",
        description="Test q parameter for reflected XSS",
        status="completed",
        result="safe",
        severity=None,
        required_agent="pentester",
    )
    register_hypothesis(
        hypothesis_id="hyp-003",
        session_id=sid,
        title="Test IDOR on /api/users",
        description="Check if user IDs are guessable",
        status="pending",
        result=None,
        required_agent="pentester",
    )

    register_finding(
        finding_id="find-001",
        session_id=sid,
        title="SQL Injection in Login",
        description="username param vulnerable to time-based SQLi",
        severity="critical",
        status="confirmed",
        location="/login",
        parameter="username",
        evidence="admin' AND SLEEP(5)-- → 5s delay",
        vulnerability_type="sqli",
        cwe_id="CWE-89",
        hypothesis_id="hyp-001",
        discovered_by="pentester",
    )
    register_finding(
        finding_id="find-002",
        session_id=sid,
        title="Missing CSRF Token",
        description="Login form has no CSRF protection",
        severity="medium",
        status="confirmed",
        location="/login",
        vulnerability_type="csrf",
        cwe_id="CWE-352",
        discovered_by="recon",
    )

    return sid


# ===================================================================
# PART 1: Data store unit tests (no server, no LLM, no Docker)
# ===================================================================

class TestDashboardDataStore:
    """Test the in-memory data store functions directly."""

    def test_register_session(self):
        register_test_session("s1", "http://example.com")
        assert "s1" in _test_sessions
        assert _test_sessions["s1"]["target_url"] == "http://example.com"
        assert _test_sessions["s1"]["status"] == "running"

    def test_complete_session(self):
        register_test_session("s1", "http://example.com")
        complete_test_session("s1", success=True)
        assert _test_sessions["s1"]["status"] == "completed"
        assert _test_sessions["s1"]["completed_at"] is not None

    def test_complete_session_failure(self):
        register_test_session("s1", "http://example.com")
        complete_test_session("s1", success=False)
        assert _test_sessions["s1"]["status"] == "failed"

    def test_register_hypothesis(self):
        register_test_session("s1", "http://example.com")
        register_hypothesis(
            hypothesis_id="h1",
            session_id="s1",
            title="Test SQLi",
            description="Inject on /login",
        )
        assert "h1" in _hypotheses
        assert _hypotheses["h1"]["title"] == "Test SQLi"
        assert _test_sessions["s1"]["hypothesis_count"] == 1

    def test_hypothesis_idempotent(self):
        """Registering same hypothesis twice should not double-count."""
        register_test_session("s1", "http://example.com")
        register_hypothesis("h1", "s1", "Test SQLi")
        register_hypothesis("h1", "s1", "Test SQLi v2")  # update
        assert _test_sessions["s1"]["hypothesis_count"] == 1
        assert _hypotheses["h1"]["title"] == "Test SQLi v2"

    def test_register_finding(self):
        register_test_session("s1", "http://example.com")
        register_finding(
            finding_id="f1",
            session_id="s1",
            title="SQLi Found",
            description="Time-based blind SQLi",
            severity="critical",
        )
        assert "f1" in _findings
        assert _findings["f1"]["severity"] == "critical"
        assert _test_sessions["s1"]["findings_count"] == 1

    def test_finding_idempotent(self):
        register_test_session("s1", "http://example.com")
        register_finding("f1", "s1", "SQLi", "desc", "critical")
        register_finding("f1", "s1", "SQLi v2", "desc2", "high")
        assert _test_sessions["s1"]["findings_count"] == 1
        assert _findings["f1"]["title"] == "SQLi v2"

    def test_sync_dashboard_data_flow(self):
        """Simulate what run.py's _sync_dashboard_data does."""
        sid = "flow-test"
        register_test_session(sid, "http://target.local")

        # Simulate hypothesis_manager tree from graph state
        hyp_tree = {
            "abc123": {
                "title": "Test SSTI on /template",
                "description": "Jinja2 template injection",
                "status": "completed",
                "result": "vulnerable",
                "severity": "critical",
                "required_agent": "pentester",
            },
            "def456": {
                "title": "Check auth bypass",
                "description": "JWT none algorithm",
                "status": "pending",
                "result": None,
                "severity": None,
                "required_agent": "pentester",
            },
        }

        # Simulate correlation_store findings
        findings_dict = {
            "f-001": {
                "title": "SSTI Confirmed",
                "description": "{{7*7}} returns 49",
                "severity": "critical",
                "status": "confirmed",
                "location": "/template",
                "parameter": "name",
                "evidence": "{{7*7}} → 49",
                "vulnerability_type": "ssti",
                "cwe_id": "CWE-94",
                "hypothesis_id": "abc123",
                "discovered_by": "pentester",
            }
        }

        # Do what _sync_dashboard_data does
        for hyp_id, hyp_dict in hyp_tree.items():
            register_hypothesis(
                hypothesis_id=str(hyp_id),
                session_id=sid,
                title=hyp_dict.get("title", ""),
                description=hyp_dict.get("description", ""),
                status=hyp_dict.get("status", "pending"),
                result=hyp_dict.get("result"),
                severity=hyp_dict.get("severity"),
                required_agent=hyp_dict.get("required_agent", "pentester"),
            )
        for find_id, find_dict in findings_dict.items():
            register_finding(
                finding_id=str(find_id),
                session_id=sid,
                title=find_dict.get("title", ""),
                description=find_dict.get("description", ""),
                severity=find_dict.get("severity", "info"),
                status=find_dict.get("status", "potential"),
                location=find_dict.get("location", ""),
                parameter=find_dict.get("parameter", ""),
                evidence=find_dict.get("evidence", ""),
                vulnerability_type=find_dict.get("vulnerability_type", ""),
                cwe_id=find_dict.get("cwe_id"),
                hypothesis_id=find_dict.get("hypothesis_id"),
                discovered_by=find_dict.get("discovered_by", ""),
            )

        # Verify
        assert len(_hypotheses) == 2
        assert len(_findings) == 1
        assert _test_sessions[sid]["hypothesis_count"] == 2
        assert _test_sessions[sid]["findings_count"] == 1
        assert _hypotheses["abc123"]["result"] == "vulnerable"
        assert _findings["f-001"]["severity"] == "critical"


# ===================================================================
# PART 2: REST API endpoint tests (FastAPI TestClient, no LLM)
# ===================================================================

class TestDashboardAPI:
    """Test dashboard REST endpoints via httpx AsyncClient."""

    @pytest.mark.asyncio
    async def test_health(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/health")
            assert resp.status_code == 200
            assert resp.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_stats_empty(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/dashboard/stats")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_vulnerabilities"] == 0
            assert data["total_tests"] == 0

    @pytest.mark.asyncio
    async def test_stats_with_data(self, app, seed_session):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/dashboard/stats")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_tests"] == 1
            assert data["critical_count"] == 1
            assert data["medium_count"] == 1
            assert data["total_vulnerabilities"] == 2

    @pytest.mark.asyncio
    async def test_tests_list(self, app, seed_session):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/dashboard/tests")
            assert resp.status_code == 200
            tests = resp.json()
            assert len(tests) == 1
            assert tests[0]["target_url"] == "http://target.local:9000"

    @pytest.mark.asyncio
    async def test_test_detail(self, app, seed_session):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/api/dashboard/tests/{seed_session}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == seed_session
            assert data["hypothesis_count"] == 3
            assert data["findings_count"] == 2

    @pytest.mark.asyncio
    async def test_test_detail_404(self, app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/dashboard/tests/nonexistent")
            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_hypotheses_all(self, app, seed_session):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/dashboard/hypotheses")
            assert resp.status_code == 200
            hyps = resp.json()
            assert len(hyps) == 3

    @pytest.mark.asyncio
    async def test_hypotheses_by_session(self, app, seed_session):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/api/dashboard/hypotheses?session_id={seed_session}")
            assert resp.status_code == 200
            hyps = resp.json()
            assert len(hyps) == 3

            # Verify hypothesis details
            titles = {h["title"] for h in hyps}
            assert "Test SQL Injection on /login" in titles
            assert "Check XSS on /search" in titles

            # Verify statuses
            statuses = {h["id"]: h["status"] for h in hyps}
            assert statuses["hyp-001"] == "completed"
            assert statuses["hyp-003"] == "pending"

            # Verify results
            results = {h["id"]: h["result"] for h in hyps}
            assert results["hyp-001"] == "vulnerable"
            assert results["hyp-002"] == "safe"
            assert results["hyp-003"] is None

    @pytest.mark.asyncio
    async def test_hypotheses_empty_session(self, app, seed_session):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/dashboard/hypotheses?session_id=nonexistent")
            assert resp.status_code == 200
            assert resp.json() == []

    @pytest.mark.asyncio
    async def test_findings_all(self, app, seed_session):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/dashboard/findings")
            assert resp.status_code == 200
            findings = resp.json()
            assert len(findings) == 2

    @pytest.mark.asyncio
    async def test_findings_by_session(self, app, seed_session):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/api/dashboard/findings?session_id={seed_session}")
            assert resp.status_code == 200
            findings = resp.json()
            assert len(findings) == 2

            # Verify finding details
            sqli = next(f for f in findings if f["id"] == "find-001")
            assert sqli["severity"] == "critical"
            assert sqli["location"] == "/login"
            assert sqli["cwe_id"] == "CWE-89"
            assert sqli["hypothesis_id"] == "hyp-001"
            assert "SLEEP" in sqli["evidence"]

    @pytest.mark.asyncio
    async def test_findings_filter_severity(self, app, seed_session):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/api/dashboard/findings?severity=critical")
            assert resp.status_code == 200
            findings = resp.json()
            assert len(findings) == 1
            assert findings[0]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_severity_distribution(self, app, seed_session):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/dashboard/severity-distribution")
            assert resp.status_code == 200
            dist = resp.json()
            assert dist["critical"] == 1
            assert dist["medium"] == 1
            assert dist["high"] == 0

    @pytest.mark.asyncio
    async def test_trends(self, app, seed_session):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/dashboard/trends?days=7")
            assert resp.status_code == 200
            trends = resp.json()
            assert len(trends) == 8  # 7 days + today
            # Latest day should have our findings
            latest = trends[-1]
            assert latest["critical"] >= 1

    @pytest.mark.asyncio
    async def test_session_lifecycle(self, app):
        """Test the full session lifecycle through the API."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Start with empty
            resp = await client.get("/api/dashboard/stats")
            assert resp.json()["total_tests"] == 0

            # 2. Register session (simulating what run.py does)
            register_test_session("lifecycle-1", "http://vuln.local")

            resp = await client.get("/api/dashboard/stats")
            assert resp.json()["total_tests"] == 1
            assert resp.json()["running_tests"] == 1

            # 3. Add hypothesis
            register_hypothesis("h1", "lifecycle-1", "Test SQLi", status="in_progress")

            resp = await client.get("/api/dashboard/hypotheses?session_id=lifecycle-1")
            hyps = resp.json()
            assert len(hyps) == 1
            assert hyps[0]["status"] == "in_progress"

            # 4. Add finding
            register_finding("f1", "lifecycle-1", "SQLi", "Found it", "critical")

            resp = await client.get("/api/dashboard/findings?session_id=lifecycle-1")
            findings = resp.json()
            assert len(findings) == 1

            # 5. Update hypothesis to completed
            register_hypothesis(
                "h1", "lifecycle-1", "Test SQLi",
                status="completed", result="vulnerable", severity="critical",
            )

            resp = await client.get("/api/dashboard/hypotheses?session_id=lifecycle-1")
            hyps = resp.json()
            assert hyps[0]["status"] == "completed"
            assert hyps[0]["result"] == "vulnerable"

            # 6. Complete session
            complete_test_session("lifecycle-1", success=True)

            resp = await client.get("/api/dashboard/stats")
            assert resp.json()["running_tests"] == 0
            assert resp.json()["critical_count"] == 1


# ===================================================================
# PART 3: Live E2E with OpenRouter + Docker
# ===================================================================

def _has_docker():
    """Check if Docker is available."""
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "info"], capture_output=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def _has_docker_image():
    """Check if fennec-linux image exists."""
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", "fennec-linux"],
            capture_output=True, timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")


@pytest.mark.asyncio
@pytest.mark.skipif(
    not _has_docker() or not _has_docker_image() or not OPENROUTER_KEY,
    reason="Requires Docker + fennec-linux image + OPENROUTER_API_KEY env var",
)
class TestLiveE2E:
    """Full end-to-end test with real LLM and Docker.

    Uses mistralai/mistral-small-3.1-24b-instruct via OpenRouter ($0.14/1M tokens).
    Requires Docker running and fennec-linux image built.
    """

    async def test_full_pentest_sse_to_dashboard(self):
        """Start a pentest via SSE, verify hypotheses appear in dashboard."""

        # Configure environment for OpenRouter
        os.environ["LLM_PROVIDER"] = "openrouter"
        os.environ["LLM_MODEL"] = "mistralai/mistral-small-3.1-24b-instruct"
        os.environ["OPENROUTER_API_KEY"] = OPENROUTER_KEY

        # Clear caches so config picks up new env vars
        from src.config.settings import get_config
        get_config.cache_clear()

        # Import create_app lazily (triggers graph compilation)
        from run import create_app
        app = create_app()

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            timeout=300,  # 5 min for full pentest
        ) as client:

            # Trigger startup event
            await app.router.startup()

            try:
                # Start pentest against a simple target
                # Using httpbin.org as a safe, public target
                resp = await client.post(
                    "/api/pentest/start",
                    json={"target_url": "https://httpbin.org"},
                )
                assert resp.status_code == 200

                # Parse SSE events
                session_id = None
                events_received = []
                node_updates = []

                body = resp.text
                for line in body.split("\n"):
                    if line.startswith("event: "):
                        event_type = line[7:].strip()
                    elif line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                        except json.JSONDecodeError:
                            continue

                        events_received.append(event_type)

                        if event_type == "session_start":
                            session_id = data.get("session_id")
                        elif event_type == "node_update":
                            node_updates.append(data.get("node", ""))

                # --- Assertions ---

                # Must have received session_start
                assert session_id is not None, "No session_start event received"
                assert "session_start" in events_received

                # Must have gone through recon → analyst at minimum
                assert "recon" in node_updates, f"Recon never ran. Nodes: {node_updates}"
                assert "analyst" in node_updates, f"Analyst never ran. Nodes: {node_updates}"

                # Verify dashboard has the session
                resp = await client.get("/api/dashboard/stats")
                stats = resp.json()
                assert stats["total_tests"] >= 1

                # Verify test detail exists
                resp = await client.get(f"/api/dashboard/tests/{session_id}")
                assert resp.status_code == 200
                test_data = resp.json()
                assert test_data["target_url"] == "https://httpbin.org"

                # Verify hypotheses were synced
                resp = await client.get(
                    f"/api/dashboard/hypotheses?session_id={session_id}"
                )
                hyps = resp.json()
                print(f"\n=== HYPOTHESES ({len(hyps)}) ===")
                for h in hyps:
                    print(f"  [{h['status']}] {h['title']} → {h.get('result', '-')}")

                # Analyst should have created at least 1 hypothesis
                assert len(hyps) >= 1, "No hypotheses synced to dashboard"

                # If pentester ran, check for findings
                if "pentester" in node_updates:
                    resp = await client.get(
                        f"/api/dashboard/findings?session_id={session_id}"
                    )
                    findings = resp.json()
                    print(f"\n=== FINDINGS ({len(findings)}) ===")
                    for f in findings:
                        print(f"  [{f['severity']}] {f['title']} @ {f['location']}")

                # Must have completed or errored
                assert "complete" in events_received or "error" in events_received

                print(f"\n=== SUMMARY ===")
                print(f"Session: {session_id}")
                print(f"Events: {len(events_received)}")
                print(f"Nodes: {' → '.join(node_updates)}")
                print(f"Hypotheses: {len(hyps)}")

            finally:
                # Cleanup
                await app.router.shutdown()

                # Reset env
                os.environ.pop("LLM_PROVIDER", None)
                os.environ.pop("LLM_MODEL", None)
                os.environ.pop("OPENROUTER_API_KEY", None)
                get_config.cache_clear()
