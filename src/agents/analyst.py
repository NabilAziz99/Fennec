"""
Analyst Agent - Forms hypotheses and analyzes results.

Uses LangChain's create_agent with:
1. No execution tools (pure reasoning agent)
2. Built-in middleware (ToolRetryMiddleware, ModelCallLimitMiddleware)
3. Structured output via ToolStrategy(AnalystResult) — all analysis in one response

Combines the roles of:
- Hypothesis Former: Creates attack theories from recon data
- Correlator: Analyzes test results and identifies patterns
"""

import logging
import os
import uuid
from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    ToolRetryMiddleware,
)

try:
    from ..middleware.budget_aware_prompt import BudgetAwarePromptMiddleware
    from ..middleware.finalizeBeforeModelLimitMiddleware import FinalizeBeforeModelLimitMiddleware
    from ..middleware.truncate_tool_outputs import TruncateOldToolOutputsMiddleware
except ImportError:
    from src.middleware.budget_aware_prompt import BudgetAwarePromptMiddleware
    from src.middleware.finalizeBeforeModelLimitMiddleware import FinalizeBeforeModelLimitMiddleware
    from src.middleware.truncate_tool_outputs import TruncateOldToolOutputsMiddleware

try:
    from ..state import FennecState, ReconData, CorrelationStore
    from ..state.hypothesis import Hypothesis, AgentRole, HypothesisStatus, HypothesisResult
    from ..state.correlation import Finding, FindingSeverity, FindingStatus
    from ..state.agent_result import AgentResult
    from ..orchestration import HypothesisManager
    from ..schemas.analyst_result import AnalystResult
    from ..cli import (
        print_agent_header, print_hypothesis_added,
        print_hypothesis_tree,
    )
except ImportError:
    from src.state import FennecState, ReconData, CorrelationStore
    from src.state.hypothesis import Hypothesis, AgentRole, HypothesisStatus, HypothesisResult
    from src.state.correlation import Finding, FindingSeverity, FindingStatus
    from src.state.agent_result import AgentResult
    from src.orchestration import HypothesisManager
    from src.schemas.analyst_result import AnalystResult
    from src.cli import (
        print_agent_header, print_hypothesis_added,
        print_hypothesis_tree,
    )

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Static skill → OWASP Top 10 mapping
# ---------------------------------------------------------------------------

SKILL_TO_OWASP: dict[str, str] = {
    # A01 Broken Access Control
    "idor": "A01",
    "broken_function_level_authorization": "A01",
    "mass_assignment": "A01",
    "csrf": "A01",
    "open_redirect": "A01",
    "path_traversal_lfi_rfi": "A01",
    # A02 Cryptographic Failures
    "authentication_jwt": "A02",
    # A03 Injection
    "sql_injection": "A03",
    "xss": "A03",
    "xxe": "A03",
    "rce": "A03",
    # A05 Security Misconfiguration
    "information_disclosure": "A05",
    "insecure_file_uploads": "A05",
    "subdomain_takeover": "A05",
    # A07 Identification & Authentication Failures
    "broken_auth": "A07",
    # A08 Software & Data Integrity Failures
    "business_logic": "A08",
    # A10 SSRF
    "ssrf": "A10",
    # A11 (custom) Race Conditions
    "race_conditions": "A04",
}


def _derive_owasp_category(skills: list[str]) -> str:
    """Derive the best OWASP category from a list of skill names."""
    for skill in skills:
        normalized = skill.lower().replace("-", "_").replace(" ", "_")
        if normalized in SKILL_TO_OWASP:
            return SKILL_TO_OWASP[normalized]
    return ""


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

def get_analyst_prompt(
    target_url: str,
    recon_data: ReconData = None,
    existing_hypotheses: list[Hypothesis] = None,
    correlation_store: CorrelationStore = None,
    pending_result: dict = None,
    task_description: str | None = None,
    task_hint: str | None = None,
) -> str:
    """Generate the analyst agent system prompt with structured output instructions."""

    # Recon data section
    recon_section = ""
    if recon_data:
        recon_section = f"""
## RECON DATA
{recon_data.get_summary()}
"""

    # Hardcoded skills with descriptions (from skills/knowledge/*.md frontmatter)
    skills_section = """
## AVAILABLE SKILLS (for hypothesis testing)

### Vulnerabilities
- **sql-injection**: SQL injection testing covering union, blind, error-based, and ORM bypass techniques
- **xss**: XSS testing covering reflected, stored, and DOM-based vectors with CSP bypass techniques
- **idor**: IDOR/BOLA testing for object-level authorization failures and cross-account data access
- **authentication-jwt**: JWT and OIDC security testing covering token forgery, algorithm confusion, and claim manipulation
- **rce**: RCE testing covering command injection, deserialization, template injection, and code evaluation
- **ssrf**: SSRF testing for cloud metadata access, internal service discovery, and protocol smuggling
- **csrf**: CSRF testing covering token bypass, SameSite cookies, CORS misconfigurations, and state-changing request abuse
- **xxe**: XXE testing for external entity injection, file disclosure, and SSRF via XML parsers
- **path-traversal-lfi-rfi**: Path traversal and file inclusion testing for local/remote file access and code execution
- **insecure-file-uploads**: File upload security testing covering extension bypass, content-type manipulation, and path traversal
- **open-redirect**: Open redirect testing for phishing pivots, OAuth token theft, and allowlist bypass
- **race-conditions**: Race condition testing for TOCTOU bugs, double-spend, and concurrent state manipulation
- **mass-assignment**: Mass assignment testing for unauthorized field binding and privilege escalation via API parameters
- **information-disclosure**: Information disclosure testing covering error messages, debug endpoints, metadata leakage, and source exposure
- **business-logic**: Business logic testing for workflow bypass, state manipulation, and domain invariant violations
- **broken-function-level-authorization**: BFLA testing for action-level authorization failures across endpoints, admin functions, and API operations
- **subdomain-takeover**: Subdomain takeover testing for dangling DNS records and unclaimed cloud resources

### Frameworks & Technologies
- **fastapi**: Security testing playbook for FastAPI applications covering ASGI, dependency injection, and API vulnerabilities
- **nextjs**: Security testing playbook for Next.js covering App Router, Server Actions, RSC, and Edge runtime vulnerabilities
- **firebase-firestore**: Firebase/Firestore security testing covering security rules, Cloud Functions, and client-side trust issues
- **supabase**: Supabase security testing covering Row Level Security, PostgREST, Edge Functions, and service key exposure
- **graphql**: GraphQL security testing covering introspection, resolver injection, batching attacks, and authorization bypass
"""

    # Existing hypotheses section
    hypotheses_section = ""
    if existing_hypotheses:
        hypotheses_section = "\n## EXISTING HYPOTHESES\n"
        for h in existing_hypotheses[:15]:
            status = h.status.value if h.status else "pending"
            result = ""
            if h.result:
                result = f" → {h.result.value}"
            hypotheses_section += f"- [{status}{result}] {h.title}\n"

    # Findings section (from correlation store)
    findings_section = ""
    if correlation_store and correlation_store.findings:
        findings_section = "\n## TEST FINDINGS\n"
        for f in list(correlation_store.findings.values())[:15]:
            findings_section += f"- [{f.severity.value}] {f.title} at {f.location}\n"
            if f.vulnerability_type:
                findings_section += f"  Type: {f.vulnerability_type}\n"

    # Pending result from pentester
    result_section = ""
    if pending_result:
        result_section = f"""
## LATEST TEST RESULT
Status: {pending_result.get('status', 'unknown')}
Result: {pending_result.get('result', 'unknown')}
Findings: {pending_result.get('findings', [])}
"""

    task_context = ""
    if task_description or task_hint:
        details = []
        if task_description:
            details.append(f"Objective: {task_description}")
        if task_hint:
            details.append(f"Hint: {task_hint}")
        task_context = f"""
## TASK CONTEXT
{chr(10).join(details)}
"""

    return f"""# SECURITY ANALYST

You are an expert security analyst for authorized penetration testing.
QUALITY HYPOTHESES lead to QUALITY FINDINGS - be specific and actionable.

## TARGET
{target_url}
{recon_section}
{skills_section}
{hypotheses_section}
{findings_section}
{result_section}
{task_context}
## YOUR MISSION

You have TWO jobs depending on the current state:

### JOB 1: Analyze results from Reconnaissance Agent and Pentester Agent. 
Analyze the findings and look for:
1. **Attack Chains** - How can vulnerabilities be chained for maximum impact?
2. **Patterns** - Are similar issues appearing in multiple places?
3. **Gaps** - What areas haven't been tested yet?
4. **DECIDE**  if you have enough information to form STRONG HYPOTHESES. If not, request more recon from the Reconnaissance Agent.

IF YOU HAVE ENOUGH INFORMATION TO FORM STRONG HYPOTHESES, PROCEED TO JOB 2.

### JOB 2: Form Hypotheses (when you have recon data but few/no hypotheses)
Analyze the recon data and form SPECIFIC attack hypotheses:
1. IDENTIFY what vulnerabilities might exist (IDOR, SQLi, SSRF, XSS, RCE, etc.)
2. LOCATE exactly where (endpoint, parameter, input field)
3. SPECIFY skills/knowledge needed to test them
4. PRIORITIZE by potential impact (critical > high > medium > low)

Focus on HIGH-IMPACT vulnerabilities:
- IDOR, SQLi, SSRF, XSS, XXE, RCE, CSRF, Race Conditions, Business Logic, Auth/JWT


## HOW TO REPORT
You have NO execution tools — you are a pure reasoning agent.
Think through the data, then produce ONE structured response containing:
- summary: Brief summary of your analysis
- hypotheses: New attack hypotheses to add (title, description, skills, priority, location, attack_vector)
- recon_request/recon_reason: If you need more recon on a specific area
- notes: Free-form observations

## RULES
- Base hypotheses on ACTUAL recon findings or test results
- Be SPECIFIC about location and attack vector - vague hypotheses waste time
- Generate ONE hypothesis per applicable OWASP Top 10 category:
  A01 Broken Access Control, A02 Cryptographic Failures, A03 Injection,
  A04 Insecure Design, A05 Security Misconfiguration, A06 Vulnerable/Outdated Components,
  A07 Identification & Authentication Failures, A08 Software & Data Integrity Failures,
  A09 Security Logging & Monitoring Failures, A10 SSRF
- For each category, if recon data suggests it COULD apply, create a hypothesis
- Skip categories clearly inapplicable based on recon (justify why in description)
- Prioritize by expected impact (critical > high > medium)
- Consider attack chains (SQLi → data access → privilege escalation)
- Don't duplicate existing hypotheses
- Only set recon_request if you cannot form at least ONE testable hypothesis
  OR if a specific missing detail blocks testing

## BEGIN ANALYSIS
Analyze the available data and produce your structured response. Be SPECIFIC."""


# ---------------------------------------------------------------------------
# Process pending result from pentester
# ---------------------------------------------------------------------------

def _process_pending_result(
    pending_result: dict,
    current_hypothesis_id: str,
    manager: HypothesisManager,
    correlation_store: CorrelationStore,
) -> None:
    """
    Process a pentester's pending_agent_result into hypothesis status + findings.

    Delegates status handling, output registration, and unblocking to
    ``manager.handle_result()``.  Separately creates findings in the
    CorrelationStore (the manager doesn't touch it).

    Updates manager and correlation_store in place.
    """
    if not pending_result or not current_hypothesis_id:
        return

    if current_hypothesis_id not in manager.tree.hypotheses:
        return

    hyp = manager.tree.hypotheses[current_hypothesis_id]

    # Reconstruct AgentResult from the pending_result dict
    agent_result = AgentResult(
        status=pending_result.get("status", "completed"),
        result=pending_result.get("result"),
        severity=pending_result.get("severity"),
        outputs=pending_result.get("outputs", []),
        findings=pending_result.get("findings", []),
        suggested_followups=pending_result.get("suggested_followups", []),
        needs=pending_result.get("needs", []),
        error=pending_result.get("error"),
    )

    # Delegate to manager: updates status, result, severity, outputs_registry,
    # and unblocks any hypotheses waiting on this one's outputs.
    manager.current_hypothesis_id = current_hypothesis_id
    manager.handle_result(agent_result)

    # Add findings to correlation store (manager doesn't handle this)
    for finding_text in pending_result.get("findings", []):
        severity_value = pending_result.get("severity") or "info"
        finding = Finding(
            id=str(uuid.uuid4())[:8],
            title=finding_text[:100],
            description=finding_text,
            location=hyp.title,
            severity=FindingSeverity(severity_value),
            status=FindingStatus.CONFIRMED,
            hypothesis_id=current_hypothesis_id,
        )
        correlation_store.add_finding(finding)


# ---------------------------------------------------------------------------
# Populate state from structured output
# ---------------------------------------------------------------------------

def _populate_analyst_data(
    structured: AnalystResult,
    manager: HypothesisManager,
    correlation_store: CorrelationStore,
) -> dict | None:
    """
    Create hypotheses from AnalystResult.

    Returns agent_request dict if recon was requested, else None.
    """
    # Add hypotheses
    for h_data in structured.hypotheses:
        hypothesis = Hypothesis(
            title=h_data.title,
            description=h_data.description,
            required_agent=AgentRole.PENTESTER,
            skills=h_data.skills,
            owasp_category=_derive_owasp_category(h_data.skills),
            priority=h_data.priority,
            expected_outputs=h_data.expected_outputs,
        )
        manager.add_hypothesis(hypothesis)
        print_hypothesis_added({
            "title": hypothesis.title,
            "required_agent": "pentester",
            "priority": hypothesis.priority,
        })

    # Build recon request if needed
    agent_request = None
    has_pending = any(
        h.status is None or h.status.value == "pending"
        for h in manager.tree.hypotheses.values()
    )
    if structured.recon_request and not has_pending:
        agent_request = {
            "from": "analyst",
            "to": "recon",
            "task": structured.recon_request,
            "context": structured.recon_reason or "",
        }

    return agent_request


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

async def analyst_node(
    state: FennecState,
    config: RunnableConfig,
) -> dict[str, Any]:
    """Analyst agent node — forms hypotheses and analyzes results.

    Uses ``create_agent`` with:
    * **ToolRetryMiddleware** — catches tool errors, returns message to LLM
    * **ModelCallLimitMiddleware** — caps iterations at 15
    * **ToolStrategy(AnalystResult)** — all analysis in one structured response

    Tools: **none** (analyst is pure reasoning)
    """
    print_agent_header("analyst")

    configurable = config.get("configurable", {})
    llm = configurable.get("llm_analyst") or configurable.get("llm")

    if not llm:
        from ..config.settings import get_default_llm, get_config, create_llm
        cfg = get_config()
        llm = create_llm(cfg.analyst_llm_model) if cfg.analyst_llm_model else get_default_llm()

    # ---- restore state ----
    recon_data = None
    if state.get("recon_data"):
        recon_data = ReconData.from_dict(state["recon_data"])

    manager = None
    if state.get("hypothesis_manager"):
        manager = HypothesisManager.from_dict(state["hypothesis_manager"])
    else:
        manager = HypothesisManager()

    existing_hypotheses = list(manager.tree.hypotheses.values()) if manager else []

    correlation_store = None
    if state.get("correlation_store"):
        correlation_store = CorrelationStore.from_dict(state["correlation_store"])
    else:
        correlation_store = CorrelationStore()

    # ---- system prompt ----
    system_prompt = get_analyst_prompt(
        target_url=state.get("target_url", ""),
        recon_data=recon_data,
        existing_hypotheses=existing_hypotheses,
        correlation_store=correlation_store,
        pending_result=None,
        task_description=state.get("task_description"),
        task_hint=state.get("task_hint"),
    )

    # ---- tools: none — analyst is pure reasoning, no planning tool needed ----
    tools = []

    # ---- build agent ----
    analyst_call_limit = configurable.get("method_preset", {}).get("analyst_model_calls", int(os.getenv("ANALYST_MODEL_CALL_LIMIT", "20")))
    # Bump max_tokens on the analyst LLM. AnalystResult contains a
    # `hypotheses` array — for a target with several attack surfaces this
    # serializes to a sizable JSON tool-call payload. Default 4096 tokens
    # was truncating the emission, parsing returned an empty/partial
    # AnalystResult, and the orchestrator saw 0 hypotheses → ended the
    # run after recon. Same root cause as recon/pentester extraction
    # truncation. model_copy mutates the underlying field so it persists
    # through ToolStrategy's tool re-binding.
    try:
        llm = llm.model_copy(update={"max_tokens": 16384})
    except Exception:  # pragma: no cover - older LC / non-pydantic models
        pass
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        middleware=[
            ToolRetryMiddleware(max_retries=1, on_failure="continue"),
            TruncateOldToolOutputsMiddleware(agent_name="analyst"),
            BudgetAwarePromptMiddleware(run_limit=analyst_call_limit),
            FinalizeBeforeModelLimitMiddleware(run_limit=analyst_call_limit, buffer=3, structured_tool_name="AnalystResult"),
            ModelCallLimitMiddleware(run_limit=analyst_call_limit, exit_behavior="end"),
        ],
        response_format=ToolStrategy(AnalystResult),
        name="analyst",
    )

    # ---- invoke (fresh messages) ----
    try:
        result = await agent.ainvoke(
            {"messages": []},
            config=config,
        )
    except Exception as exc:
        logger.warning("Analyst agent invocation error (likely model-call limit): %s", exc)
        result = {"messages": [], "structured_response": None}

    # ---- populate from structured response ----
    agent_request = None
    structured: AnalystResult | None = result.get("structured_response")
    if structured is not None:
        agent_request = _populate_analyst_data(
            structured=structured,
            manager=manager,
            correlation_store=correlation_store,
        )

        # Print hypothesis tree
        hypotheses_list = [
            {
                "id": h.id,
                "title": h.title,
                "description": getattr(h, "description", None),
                "skills": list(getattr(h, "skills", None) or []),
                "owasp_category": getattr(h, "owasp_category", ""),
                "status": h.status.value if h.status else "pending",
                "required_agent": "pentester",
                "priority": h.priority,
            }
            for h in manager.tree.hypotheses.values()
        ]

        print_hypothesis_tree(hypotheses_list)

    # ---- return state updates ----
    return {
        "messages": result["messages"],
        "hypothesis_manager": manager.to_dict(),
        "correlation_store": correlation_store.to_dict(),
        "agent_request": agent_request,
    }
