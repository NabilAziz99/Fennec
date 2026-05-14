"""
Recon Agent - Initial reconnaissance specialist.

Uses LangChain's create_agent with:
1. Explicit tool list (terminal, browser — execution only)
2. Built-in middleware (ToolRetryMiddleware, TodoListMiddleware, ModelCallLimitMiddleware)
3. Structured output via ToolStrategy(ReconResult) — all findings in one response
"""

import asyncio
import logging
import os
import threading
import time
from typing import Any
from datetime import datetime, timezone

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, SystemMessage
try:
    from langchain_core.callbacks import BaseCallbackHandler
except ImportError:  # pragma: no cover - fallback for older path
    from langchain_core.callbacks.base import BaseCallbackHandler

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    TodoListMiddleware,
    ToolRetryMiddleware,
)

try:
    from ..state import FennecState, ReconData
    from ..state.recon import (
        CanonicalAccess,
        Component,
        ComponentType,
        Endpoint,
        Technology,
        TechnologyType,
        EntryPoint,
        VulnCandidate,
    )
    from ..schemas.recon_result import ReconResult
    from ..tools.execution import create_terminal_tool, create_browser_tool, create_web_search_tool
    from ..cli import print_agent_header, print_recon_summary
    from ..prompts import build_prompt
    from ..middleware.finalizeBeforeModelLimitMiddleware import (
        FinalizeBeforeModelLimitMiddleware,
    )
    from ..middleware.budget_aware_prompt import BudgetAwarePromptMiddleware
    from ..middleware.truncate_tool_outputs import TruncateOldToolOutputsMiddleware
except ImportError:
    from src.state import FennecState, ReconData
    from src.state.recon import (
        CanonicalAccess,
        Component,
        ComponentType,
        Endpoint,
        Technology,
        TechnologyType,
        EntryPoint,
        VulnCandidate,
    )
    from src.schemas.recon_result import ReconResult
    from src.tools.execution import create_terminal_tool, create_browser_tool, create_web_search_tool
    from src.cli import print_agent_header, print_recon_summary
    from src.prompts import build_prompt
    from src.middleware.finalizeBeforeModelLimitMiddleware import (
        FinalizeBeforeModelLimitMiddleware,
    )
    from src.middleware.budget_aware_prompt import BudgetAwarePromptMiddleware
    from src.middleware.truncate_tool_outputs import TruncateOldToolOutputsMiddleware

logger = logging.getLogger(__name__)


_EXTRACTION_SYSTEM_PROMPT = (
    "You are a reconnaissance analyst. The preceding messages contain the "
    "raw tool outputs from a recon run against a web target — curl responses, "
    "whatweb/wafw00f output, gobuster results, fetched JS/HTML, API probes, "
    "etc. Your job is to produce a single ReconResult that summarises "
    "everything that was discovered.\n\n"
    "Rules:\n"
    "- Fill as many fields as the evidence supports. Leave empty lists / None "
    "for things genuinely not observed; do NOT invent data.\n"
    "- `technologies` / `components` should reflect what was detected "
    "(Server headers, JS libraries loaded, cloud providers, CDN, etc.).\n"
    "- `endpoints` and `entry_points` must only include URLs that actually "
    "returned 2xx / 3xx or are referenced by the site's own HTML/JS.\n"
    "- `vulnerability_candidates` are hypotheses worth testing, each with a "
    "concrete reason grounded in the evidence.\n"
    "- `key_findings` is a short list of the most useful takeaways.\n"
    "- `summary` is 2-4 sentences, human-readable.\n"
    "Output ONLY the ReconResult — do not call any other tools."
)


async def _extract_recon_result(llm, messages: list) -> "ReconResult | None":
    """Make a dedicated structured-output call to extract ReconResult from a
    recon agent's message history.

    This is used when the main ReAct agent finishes without emitting
    ReconResult itself (e.g. ran out of model-call budget). Running the
    extraction as its own LLM call — with an explicit system prompt and
    only the structured-output tool bound — is dramatically more reliable
    than hoping the main agent self-finalizes.
    """
    if not messages:
        return None
    # Force function_calling (tool-call based) path — the default `json_schema`
    # route calls the OpenAI SDK's client.responses.parse() which OpenRouter's
    # openai-compat shim does NOT implement, causing
    #   AttributeError: 'AsyncCompletionsWithRawResponse' object has no attribute 'parse'
    # function_calling is the older, widely-compatible structured-output mode
    # that OpenRouter (and every other tool-calling provider) supports.
    #
    # max_tokens=16384 — the ReconResult schema has 18 fields and produces a
    # big JSON payload for a real target. Default 4096 was too tight on
    # claude-sonnet-4.6 — replay against a real prod history showed it cut
    # off mid-payload (finish_reason='length', tool_calls=0) and the OpenAI
    # SDK couldn't parse the truncated JSON. We use model_copy() instead of
    # .bind(max_tokens=...) because with_structured_output() re-binds tools
    # and drops bound kwargs; model_copy actually mutates the field on the
    # underlying ChatOpenAI instance so it persists through the rebind.
    #
    # include_raw=True so we can log WHY extraction failed if it ever does
    # again — finish_reason / tool_calls count / preview all logged.
    try:
        big_llm = llm.model_copy(update={"max_tokens": 16384})
    except Exception:  # pragma: no cover - older LC / non-pydantic models
        big_llm = llm
    extractor = big_llm.with_structured_output(
        ReconResult,
        method="function_calling",
        include_raw=True,
    )
    extraction_messages = [
        SystemMessage(content=_EXTRACTION_SYSTEM_PROMPT),
        *messages,
        HumanMessage(
            content=(
                "Now produce the ReconResult structured output based on everything above."
            )
        ),
    ]
    try:
        result = await extractor.ainvoke(extraction_messages)
    except Exception as exc:
        logger.error(
            "Dedicated ReconResult extraction raised: %s (msg_count=%d)",
            exc,
            len(messages),
        )
        return None
    # include_raw=True → result is {"raw": AIMessage, "parsed": ReconResult|None,
    # "parsing_error": Exception|None}
    parsed = result.get("parsed") if isinstance(result, dict) else result
    if parsed is not None:
        return parsed
    # Diagnose the silent-None: log what the LLM actually returned so we can
    # fix whatever is preventing function_calling from working in prod.
    raw = result.get("raw") if isinstance(result, dict) else None
    parsing_error = result.get("parsing_error") if isinstance(result, dict) else None
    content_str = ""
    tool_call_count = 0
    finish_reason = None
    if raw is not None:
        raw_content = getattr(raw, "content", "")
        content_str = raw_content if isinstance(raw_content, str) else str(raw_content)
        tool_call_count = len(getattr(raw, "tool_calls", None) or [])
        finish_reason = (getattr(raw, "response_metadata", {}) or {}).get("finish_reason")
    logger.error(
        "Dedicated ReconResult extraction returned None silently "
        "(msg_count=%d parsing_error=%r finish_reason=%r "
        "tool_calls=%d content_len=%d content_preview=%r)",
        len(messages), parsing_error, finish_reason,
        tool_call_count, len(content_str), content_str[:300],
    )
    return None


def _truncate(value: Any, limit: int = 120) -> str:
    text = str(value).strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... (truncated {len(text) - limit} chars)"


def _summarize_tool_input(tool_input: Any) -> str:
    if isinstance(tool_input, dict):
        for key in ("command", "url", "query", "path", "host", "target"):
            if key in tool_input:
                return f"{key}={_truncate(tool_input[key])}"
        return _truncate(tool_input)
    return _truncate(tool_input)


def _summarize_tool_output(output: Any) -> str:
    text = str(output).strip()
    if not text:
        return "empty"
    if text.startswith("Command("):
        return "Command(...)"
    first_line = text.splitlines()[0]
    summary = _truncate(first_line)
    line_count = text.count("\n") + 1
    if line_count > 1:
        summary = f"{summary} (+{line_count - 1} lines)"
    return summary


def _format_todos(value: Any) -> str:
    todos = None
    if isinstance(value, dict) and "todos" in value:
        todos = value.get("todos")
    elif isinstance(value, list):
        todos = value
    if not isinstance(todos, list):
        return _truncate(value)

    lines: list[str] = []
    for idx, todo in enumerate(todos, start=1):
        if isinstance(todo, dict):
            status = str(todo.get("status", "")).strip()
            content = str(todo.get("content", "")).strip()
            if status:
                lines.append(f"{idx}. [{status}] {content}".strip())
            else:
                lines.append(f"{idx}. {content}".strip())
        else:
            lines.append(f"{idx}. {str(todo).strip()}")
    return "\n".join(lines)


def _fire_and_forget(coro, *, label: str = "") -> None:
    """Schedule an async coroutine from a sync callback, regardless of thread."""
    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(coro)
        logger.debug(
            "[recon][_fire_and_forget] scheduled task on RUNNING loop %s tid=%s label=%s task=%s",
            id(loop), threading.get_ident(), label, task,
        )
    except RuntimeError:
        # No running loop in this thread — run in a background thread
        logger.debug(
            "[recon][_fire_and_forget] NO running loop in tid=%s — spawning background thread label=%s",
            threading.get_ident(), label,
        )
        threading.Thread(target=asyncio.run, args=(coro,), daemon=True).start()


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

def get_recon_prompt(
    target_url: str,
    recon_data: ReconData = None,
    task: str = None,
    task_description: str | None = None,
    task_hint: str | None = None,
    auth_credentials: dict | None = None,
) -> str:
    """Generate the recon agent system prompt."""

    existing_data = ""
    if recon_data:
        existing_data = f"""
## EXISTING RECON DATA
{recon_data.get_summary()}
"""

    task_section = ""
    if task:
        task_section = f"""
## SPECIFIC TASK
{task}
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
    base = build_prompt(
        agent_type="recon",
        target_url=target_url,
        task_description=task_description,
        task_hint=task_hint,
    )
    # Make sure to add the following sections to the prompt:
    # {existing_data}
    # {task_section}
    # {task_context}
    creds_section = ""
    if auth_credentials:
        username = auth_credentials.get("username", "")
        password = auth_credentials.get("password", "")
        auth_type = auth_credentials.get("auth_type", "basic")
        creds_section = f"""
## AUTHENTICATION CREDENTIALS

You have valid credentials for the target. You MUST authenticate and explore
authenticated surface — unauthenticated reconnaissance alone is incomplete.

- Username: {username}
- Password: {password}
- Auth type hint (user-provided, verify yourself): {auth_type}

### How to actually authenticate

Step 1 — IDENTIFY the auth mechanism by reading the login page and any
JS/config it loads. Common patterns:

- **Form POST** — `<form method="post" action="/login">` with `name=email` / `name=password`
- **Supabase** — page loads `supabase-js`, calls `supabase.auth.signInWithPassword`.
  The endpoint is `{{SUPABASE_URL}}/auth/v1/token?grant_type=password` and requires an
  `apikey: {{anon_key}}` header. Both values are usually in a `supabase-config.js`
  or similar public JS file.
- **Firebase** — page loads `firebase-auth`. Signin goes to
  `https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={{api_key}}`.
- **OAuth / OIDC** — look for a `Continue with Google/GitHub/…` button; you usually
  cannot script this with curl.
- **HTTP Basic** — a 401 with `WWW-Authenticate: Basic` header on any protected URL.

Step 2 — AUTHENTICATE via the `terminal` tool:

Supabase:
```
curl -s -X POST "$SUPABASE_URL/auth/v1/token?grant_type=password" \\
  -H "apikey: $SUPABASE_ANON_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{{"email":"{username}","password":"{password}"}}' \\
  | tee /tmp/session.json
# Extract the JWT:
jq -r .access_token /tmp/session.json > /tmp/token.txt
```

Form POST + cookies:
```
curl -s -c /tmp/cookies.txt -X POST <login_url> \\
  --data-urlencode 'email={username}' \\
  --data-urlencode 'password={password}' -L -o /tmp/login_resp.html
```

HTTP Basic: add `-u '{username}:{password}'` to every request.

Step 3 — VERIFY the session is live before exploring. Hit a known-protected
endpoint (e.g. Supabase `/auth/v1/user`, or an `/api/me`-style route) and
confirm a 2xx with your real user data.

Step 4 — REUSE the session on every subsequent request for authenticated
surface area:

- Bearer/JWT:   `curl -H "Authorization: Bearer $(cat /tmp/token.txt)" <url>`
- Cookies:      `curl -b /tmp/cookies.txt <url>`
- Basic:        `curl -u '{username}:{password}' <url>`

Step 5 — EXPLORE what only a logged-in user can see: dashboards, account
settings, admin panels, billing portals, internal APIs from the OpenAPI/Swagger
spec, per-user data endpoints, etc. Record these as endpoints with an
`authenticated: true` note in your findings.

IMPORTANT: if login fails, record `default_credentials_found=false` and note
the error in your evidence — don't keep retrying with the same creds.
"""

    prompt = "\n\n".join([base, existing_data, task_section, task_context, creds_section]).strip()
    return prompt


# ---------------------------------------------------------------------------
# Hydrate ReconData from structured output
# ---------------------------------------------------------------------------

def _populate_recon_data(recon_data: ReconData, result: ReconResult) -> None:
    """Fill *recon_data* from the agent's structured response."""
    recon_data.summary = result.summary
    recon_data.priority_targets = list(result.priority_targets)
    canonical = getattr(result, "canonical_access", None)
    if canonical:
        recon_data.canonical_access = CanonicalAccess(
            scheme=canonical.scheme,
            host=canonical.host,
            port=canonical.port,
            base_path=canonical.base_path,
            host_header=canonical.host_header,
            justification=canonical.justification,
        )
    for ep in getattr(result, "endpoints", []) or []:
        recon_data.endpoints.append(Endpoint(
            path=ep.path,
            method=ep.method,
            parameters=ep.parameters,
            status_code=ep.status_code,
            content_type=ep.content_type,
            redirect_to=ep.redirect_to,
            discovered_by=ep.discovered_by,
            auth_required=ep.auth_required,
            auth_scheme=ep.auth_scheme,
            notes=ep.notes,
        ))
    for tech in getattr(result, "technologies", []) or []:
        raw_type = getattr(tech, "type", "other")
        if isinstance(raw_type, str):
            raw_type = raw_type.strip().lower() or "other"
        try:
            tech_type = TechnologyType(raw_type)
        except ValueError:
            tech_type = TechnologyType.OTHER
        recon_data.technologies.append(Technology(
            name=tech.name,
            version=getattr(tech, "version", None),
            type=tech_type,
            confidence=getattr(tech, "confidence", 0.5),
        ))
    for comp in getattr(result, "components", []) or []:
        recon_data.components.append(Component(
            name=comp.name,
            type=ComponentType(getattr(comp, "type", "other")),
            version=getattr(comp, "version", None),
            location=getattr(comp, "location", None),
            evidence_refs=getattr(comp, "evidence_refs", []) or [],
            confidence=getattr(comp, "confidence", 0.5),
            notes=getattr(comp, "notes", "") or "",
        ))
    for entry in getattr(result, "entry_points", []) or []:
        recon_data.entry_points.append(EntryPoint(
            location=entry.location,
            type=entry.type,
            input_type=getattr(entry, "input_type", "") or "",
            validation_observed=getattr(entry, "validation_observed", "") or "",
            notes=getattr(entry, "notes", "") or "",
        ))
    auth_type = getattr(result, "auth_type", None)
    if auth_type:
        recon_data.auth_type = auth_type
    login_endpoint = getattr(result, "login_endpoint", None)
    if login_endpoint:
        recon_data.login_endpoint = login_endpoint
    recon_data.registration_available = bool(getattr(result, "registration_available", False))
    recon_data.key_findings.extend(getattr(result, "key_findings", []) or [])
    for vc in getattr(result, "vulnerability_candidates", []) or []:
        recon_data.vulnerability_candidates.append(VulnCandidate(
            component=vc.component,
            detected_version=vc.detected_version,
            cve_id=vc.cve_id,
            title=vc.title,
            confidence=vc.confidence,
        ))

# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

async def recon_node(
    state: FennecState,
    config: RunnableConfig,
) -> dict[str, Any]:
    """Recon agent node — discovers the target's attack surface.

    Uses ``create_agent`` with:
    * **ToolRetryMiddleware** — catches tool errors, returns message to LLM
    * **TodoListMiddleware** — gives the agent a ``write_todos`` planning tool
    * **ModelCallLimitMiddleware** — caps iterations at 30
    * **ToolStrategy(ReconResult)** — all findings in one structured response
    """
    print_agent_header("recon")

    configurable = config.get("configurable", {})
    llm = configurable.get("llm_recon") or configurable.get("llm")

    if not llm:
        from ..config.settings import get_default_llm, get_config, create_llm
        cfg = get_config()
        llm = create_llm(cfg.recon_llm_model) if cfg.recon_llm_model else get_default_llm()

    # ---- recon data (restore or create) ----
    if state.get("recon_data"):
        recon_data = ReconData.from_dict(state["recon_data"])
    else:
        recon_data = ReconData(target_url=state.get("target_url", ""))

    # ---- optional task from another agent ----
    task = None
    agent_request = state.get("agent_request")
    if agent_request and agent_request.get("to") == "recon":
        task = agent_request.get("task", "")
        if agent_request.get("context"):
            task += f"\n\nContext: {agent_request['context']}"

    # ---- system prompt ----
    system_prompt = get_recon_prompt(
        target_url=state.get("target_url", ""),
        recon_data=recon_data,
        task=task,
        task_description=state.get("task_description"),
        task_hint=state.get("task_hint"),
        auth_credentials=state.get("auth_credentials"),
    )

    # ---- tools (explicit list — execution only) ----
    terminal = create_terminal_tool()       # shell: curl, whatweb, gobuster, subfinder, httpx, wafw00f
    browser = create_browser_tool()         # HTTP fetch & parse
    web_search = create_web_search_tool()   # web search for CVEs, exploits, research

    tools = [terminal, browser, web_search]

    # ---- build agent ----
    # Model-call budget comes directly from the method preset (turbo/balanced/deep).
    graph_recursion_limit = int(config.get("recursion_limit", 300) if config is not None else 300)
    preset = configurable.get("method_preset", {})
    model_call_budget = preset.get("recon_model_calls", int(os.getenv("RECON_MIN_MODEL_CALLS", "40")))

    # Bump max_tokens on the recon LLM. ReconResult has 18 fields including
    # `technologies`, `endpoints`, `vulnerability_candidates` arrays — on a
    # real target with many findings, claude-sonnet-4.6 emits a JSON payload
    # >4096 tokens via ToolStrategy. Default 4096 truncates the tool call
    # (finish_reason=length, no tool_calls), structured output is dropped,
    # and the rescue extractor has to retry. model_copy mutates the
    # underlying field so it persists through ToolStrategy's tool re-binding
    # (.bind() kwargs would be dropped).
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
            TodoListMiddleware(),
            TruncateOldToolOutputsMiddleware(agent_name="recon"),
            BudgetAwarePromptMiddleware(run_limit=model_call_budget),
            FinalizeBeforeModelLimitMiddleware(run_limit=model_call_budget, buffer=3, structured_tool_name="ReconResult"),
            ModelCallLimitMiddleware(run_limit=model_call_budget, exit_behavior="end"),
        ],
        response_format=ToolStrategy(ReconResult),
        name="recon",
    )

    # ---- invoke (fresh messages — don't inherit other agents' history) ----
    run_config = dict(config) if config is not None else {}
    run_config.setdefault("run_name", "recon")
    tags = list(run_config.get("tags", []))
    if "recon" not in tags:
        tags.append("recon")
    run_config["tags"] = tags
    metadata = dict(run_config.get("metadata", {}))
    metadata.setdefault("agent", "recon")
    run_config["metadata"] = metadata

    # Give the *internal agent graph* a higher recursion budget than the outer graph,
    # while still enforcing model-call budget via ModelCallLimitMiddleware.
    #
    # IMPORTANT: `config` coming from the outer role-based graph often already contains
    # `recursion_limit` (e.g. 300). Using `setdefault` would *not* override it, causing the
    # internal agent to still run with 300 super-steps and hit GraphRecursionError.
    internal_recursion_limit = max(1000, graph_recursion_limit * 4)
    existing_limit = int(run_config.get("recursion_limit", 0) or 0)
    run_config["recursion_limit"] = max(existing_limit, internal_recursion_limit)

    try:
        result = await agent.ainvoke(
            {"messages": []},
            config=run_config,
        )
    except Exception as exc:
        # ModelCallLimitMiddleware with exit_behavior="end" can crash on
        # OpenRouter/OpenAI providers that reject assistant-message prefill.
        # Recover gracefully — we still have messages from prior tool calls.
        logger.warning("Recon agent invocation error (likely model-call limit): %s", exc)
        result = {"messages": [], "structured_response": None}

    # ---- populate recon_data from structured response ----
    structured: ReconResult | None = result.get("structured_response")
    if structured is None and result.get("messages"):
        # The ReAct agent didn't emit ReconResult — either it burned its call
        # budget on tool calls or the FinalizeBeforeModelLimit prompt-injection
        # failed. Rather than losing everything we just learned, run a dedicated
        # structured-output LLM call against the accumulated message history
        # with an explicit extraction prompt. This is much more reliable than
        # forcing the agent to self-finalize in its last call.
        logger.warning(
            "Recon agent finished without structured output — extracting via dedicated call (messages=%d)",
            len(result["messages"]),
        )
        structured = await _extract_recon_result(llm, result["messages"])
    if structured is not None:
        _populate_recon_data(recon_data, structured)
        recon_data.recon_completed = datetime.now(timezone.utc)
        print_recon_summary(recon_data.to_dict())

        # ---- populate extra fields from ReconData state ----
        if recon_data:
            structured.ip_address = getattr(recon_data, "ip_address", None)
            structured.ports_open = list(getattr(recon_data, "ports_open", None) or [])
            hoi = getattr(recon_data, "headers_of_interest", None)
            if isinstance(hoi, dict):
                structured.headers_of_interest = list(hoi.keys())
            elif hoi:
                structured.headers_of_interest = list(hoi)
            structured.cookies_observed = list(getattr(recon_data, "cookies_observed", None) or [])
            structured.default_credentials_found = bool(getattr(recon_data, "default_credentials_found", False))

    # ---- always mark recon as completed so the router moves to analyst ----
    if recon_data.recon_completed is None:
        logger.warning("Recon finishing without structured output — marking completed to avoid loop")
        recon_data.recon_completed = datetime.now(timezone.utc)

    # ---- return state updates ----
    return {
        "messages": result["messages"],
        "recon_data": recon_data.to_dict(),
        "agent_request": None,  # clear the inbound request
    }
  