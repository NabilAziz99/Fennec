# CLAUDE.md — Fennec OSS

Quick orientation for AI assistants (Claude Code, Cursor, etc.) working in this repo.

## What this is

Fennec is an open-source, autonomous penetration-testing framework built on LangGraph. A multi-agent loop (Recon → Analyst → Pentester → Coder, coordinated by an Orchestrator) drives security testing against a target the user controls. Tool execution happens inside an isolated Kali Linux container.

This is the **OSS** distribution — single-user, no database, no auth, runs locally. There's a separate hosted/paid version with multi-tenant infrastructure; do not add references to it here.

## Core layout

```
agent.py                  Programmatic API: run_pentest(task) → AgentResult
cli.py / cli/main.py      CLI entrypoint (scan subcommand)
src/
  api/                    FastAPI server (server.py, job_store.py, events.py)
                          In-memory state, SSE event stream
  agents/                 Per-role nodes
    recon.py              Maps attack surface; emits ReconResult
    analyst.py            Produces a hypothesis queue from recon data
    pentester.py          Tests one hypothesis at a time; emits PentesterResult
    coder.py              Invoked by pentester for custom payload development
    human_review.py       (HTLI mode) operator approval gate after analyst
    emission.py           Terminal output for the recon-only test graph
  graph/role_based_graph.py   LangGraph wiring + routing
  tools/                  terminal, browser, file_read/write, web_search, task_tools, hypothesis_tools
  docker/client.py        aiodocker wrapper that spawns the Kali container
  prompts/                Per-agent system prompts and prompt sections
  schemas/                Pydantic models for tool I/O (recon_result, pentester_result, etc.)
  state/                  FennecState TypedDict, hypothesis/finding types, correlation store
  middleware/             LangChain middleware (model-call budget, truncation, retries)
  orchestration/          HypothesisManager
linux/                    Kali Dockerfile + tools list (run `make build` once)
frontend/                 React + Vite dashboard (optional)
```

## Key conventions

- **Imports** use the `src.*` absolute prefix. The legacy try/except `from .. import X / from src.* import X` pattern is preserved in agent files for run-from-anywhere ergonomics; keep that pattern if you add new modules under `src/agents/`.
- **Everything is async.** Tools, graph nodes, the Docker client. Use `async def` and `await`. Use `aiodocker` for container ops, `httpx` (not requests) for HTTP.
- **Tool execution always goes through the Kali container** unless `EXECUTION_MODE=local`. Never shell out to host tools from agent code.
- **Configuration is `.env` → Pydantic settings** (`src/config/settings.py`). Don't introduce new config files.
- **No persistence layer.** Findings live in the in-process `CorrelationStore` and are written to `./reports/<timestamp>_<host>/` at end of run. The FastAPI server keeps a process-local `JOBS` dict (`src/api/job_store.py`) that disappears on restart. There is no database — don't add one.
- **No auth layer.** The CLI runs anonymously, and the API server trusts whoever can reach it. Don't reintroduce a login flow.

## Adding a new tool

1. Define input schema in `src/schemas/tool_inputs.py`.
2. Implement the tool with `@tool` in the appropriate file under `src/tools/`.
3. Add the tool to the relevant agent's `tools = [...]` list in `src/agents/*.py`.
4. Make sure it executes inside the Kali container via `DockerClient.exec_in_container()` unless it's a pure-Python helper.

## Adding a new agent

1. Create `src/agents/<name>.py` with an `async def <name>_node(state, config) -> dict`.
2. Add the type to `AgentType` in `src/state/graph_state.py`.
3. Wire it in `src/graph/role_based_graph.py` (add the node, edges, and any routing logic).
4. Write a system prompt in `src/prompts/templates.py` (or a new file under `src/prompts/`).

## Testing changes

There's no test harness in this OSS distribution. To smoke-test:
- `python -m py_compile src/**/*.py` — catches syntax errors.
- `python -c "from src.graph.role_based_graph import compile_role_based_graph; compile_role_based_graph()"` — verifies the graph builds.
- `python cli.py --target http://example.com --quiet` — end-to-end run (requires Docker + an API key).

## When in doubt

The README explains usage and configuration. The architecture section there links to `docs/ARCHITECTURE.md` for deeper context. The agent prompts in `src/prompts/` are the source of truth for agent behavior — change those when you want to change how an agent acts, not the Python code.
