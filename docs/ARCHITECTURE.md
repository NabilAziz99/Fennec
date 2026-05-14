# Architecture

This document explains how Fennec is wired together at the agent and graph level. If you're trying to understand why a given decision is made, why an agent fires in a given order, or how to extend the system, start here.

## The high-level loop

```
START ─► recon ──────┐
            ▲        │
            │        ▼
       (more recon?) analyst ─► orchestrator ─┐
                                  ▲           │
                                  │           ▼
                              pentester ◄────(more hypotheses?)
                                  │
                                  ▼
                                 END (when queue is empty)
```

Three principles drive the design:

1. **Roles are specialized.** Each agent has a tight system prompt, a curated tool list, and one job. No generalist agent that does everything.
2. **Orchestration is dumb.** The orchestrator node is **not** an LLM. It's pure Python that processes the pentester's last result, updates the hypothesis tree, and picks the next node. This avoids reasoning loops and keeps cost predictable.
3. **Hypotheses are the unit of work.** The analyst doesn't pick attacks directly — it emits a queue of testable claims ("the `/api/users/{id}` endpoint may be vulnerable to IDOR"). The pentester pops one at a time, runs targeted tools, and emits a verdict.

## The four agents

### Recon (`src/agents/recon.py`)
- **Job:** Map the attack surface. Probe endpoints, identify the tech stack, enumerate subdomains, fingerprint frameworks.
- **Tools:** `terminal` (curl, whatweb, gobuster, subfinder, httpx, wafw00f), `browser` (HTTP fetch + parse), `web_search` (CVE / exploit research).
- **Output:** Structured `ReconResult` — technologies, endpoints, vulnerability candidates, observed cookies, headers of interest.
- **Re-entry:** If the analyst can't form testable hypotheses, the orchestrator can route back to recon for more data. There's a hard cap (`MAX_RECON_ROUNDS=3`) on analyst↔recon ping-pong.

### Analyst (`src/agents/analyst.py`)
- **Job:** Read recon data, emit a prioritized queue of testable hypotheses.
- **No tools.** It's a reasoning step over already-collected data.
- **Output:** A list of `Hypothesis` objects, each tagged with `required_agent` (usually pentester), `priority`, and OWASP / vulnerability-class metadata.
- **Single-shot:** Analyst runs once after recon completes (or once per recon re-run). It does *not* run between every pentester result — the orchestrator handles that.

### Pentester (`src/agents/pentester.py`)
- **Job:** Pop one hypothesis from the queue, test it, emit a verdict.
- **Tools:** `terminal`, `file_read`, `file_write`, `browser`, `web_search`, and `invoke_coder` (delegates to the coder agent for custom exploit code).
- **Output:** Structured `PentesterResult` with `status` (completed / dead_end / needs_info), `verdict` (vulnerable / not_vulnerable / inconclusive), evidence, and — when vulnerable — rich finding fields (description, impact, evidence_details, remediation, owasp_category).
- **Loop:** Pentester runs many times per scan, once per hypothesis.

### Coder (`src/agents/coder.py`)
- **Job:** Write custom exploit code or payloads when the pentester needs something the standard tools don't provide.
- **Tools:** `terminal` (test the code), `file_read`, `file_write`, `browser` (test against the target).
- **Output:** Structured `CoderResult` — file path + summary of what was built.
- **Invoked by:** The pentester via the `invoke_coder` tool (not the orchestrator). The pentester decides when custom code is necessary.

### Orchestrator (`src/graph/role_based_graph.py:orchestrator_node`)
Not an agent — pure routing logic. Each time it fires it:
1. Processes the last pentester result via `_process_pending_result` (updates the hypothesis tree, records findings).
2. Checks the hypothesis queue. If there are pending hypotheses, route to pentester. Else check if analyst requested more recon (within the cap). Else end.
3. Writes the final result and findings summary at the end of the run.

## Optional: Human-In-The-Loop (HTLI)

Set `HTLI=true` in `.env` to insert a `human_review` node between the analyst and the orchestrator. The graph pauses (via LangGraph `interrupt()`) and prompts the operator on stdin:

- Approve all pending hypotheses, or
- Reject specific ones, edit titles/priorities/descriptions, or add new hypotheses.

When the operator resumes, the orchestrator picks up with the edited queue.

## State

Everything lives in `FennecState` (a TypedDict in `src/state/graph_state.py`). The important fields:

| Field | Type | Purpose |
|---|---|---|
| `messages` | `list[BaseMessage]` | Conversation history with the `add_messages` reducer |
| `session` | `SessionContext` | Run ID, container info, language |
| `target_url` | `str` | The actual target (with `host.docker.internal` substitution applied when running in Docker mode) |
| `recon_data` | `Optional[dict]` | Serialized `ReconData` — survives across recon re-runs |
| `hypothesis_manager` | `Optional[dict]` | Serialized hypothesis tree + queue |
| `correlation_store` | `Optional[dict]` | Findings (vulnerabilities the pentester confirmed) |
| `current_hypothesis_id` | `Optional[str]` | Which hypothesis the pentester is testing right now |
| `pending_agent_result` | `Optional[dict]` | The last pentester emission, waiting for the orchestrator to process |
| `agent_request` | `Optional[dict]` | Inter-agent request — e.g. analyst asking for more recon |
| `next_agent` | `AgentType` | Set by node updates; used by the conditional routing edges |
| `should_continue` | `bool` | The orchestrator flips this to False to end the run |
| `auth_credentials` | `Optional[dict]` | Target login credentials (set via `FENNEC_AUTH_CREDENTIALS` JSON env) |
| `method` | `Optional[str]` | `turbo` / `balanced` / `deep` — drives per-agent call budgets |

## Execution modes

- `EXECUTION_MODE=docker` (default): tools run inside a long-lived Kali container, spawned per-run. Network calls leave from the container, not the host.
- `EXECUTION_MODE=local`: tools run inside the agent process directly. Useful when the agent is already inside a container (e.g. Kubernetes) and you don't want Docker-in-Docker.

The Kali image is built locally — see `linux/Dockerfile` and `linux/Makefile`. Build once with `cd linux && make build`. The default image tag is `fennec-linux` (override via `DOCKER_IMAGE`).

## Middleware

Each agent uses LangChain v1 middleware to manage cost and context:

- `ModelCallLimitMiddleware` — hard cap on LLM calls per agent run (per-method preset).
- `FinalizeBeforeModelLimitMiddleware` — injects a finalization prompt N calls before the limit, so the agent emits structured output before being cut off.
- `BudgetAwarePromptMiddleware` — annotates the system prompt with remaining call budget.
- `TruncateOldToolOutputsMiddleware` — keeps long tool outputs from blowing the context window.
- `ToolRetryMiddleware` — retries transient tool failures with `on_failure="continue"` so a single tool error doesn't kill the run.
- `TodoListMiddleware` — exposes a TODO list the agent can use for self-planning.

## Method presets

`FENNEC_METHOD` picks a preset that sets recursion limits, task timeouts, and per-agent model-call budgets:

| Preset | Recon calls | Analyst calls | Pentester calls | Task timeout |
|---|---|---|---|---|
| `turbo` | tight | tight | tight | short |
| `balanced` | medium | medium | medium | default 10 min |
| `deep` | generous | generous | generous | long |

See `get_method_preset` in `src/config/settings.py` for exact values — they may change between releases.

## What's intentionally missing in OSS

- No persistence layer. Findings are written to `./reports/<timestamp>_<host>/` at end of run. There's no database, no Postgres, no Pub/Sub queue.
- No multi-user auth. The CLI runs anonymously. There's no login, no user record, no quota.
- No managed worker pool. One scan at a time, in the local Python process.

The hosted version adds all of these (managed Postgres, Pub/Sub job queue, multi-tenant auth, autoscaled worker pods) without changing the agent code. If you're contributing here, you don't need to think about that infrastructure — the agent core is the same.
