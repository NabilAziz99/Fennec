# Fennec

An open-source, AI-driven penetration testing framework. Fennec runs a multi-agent loop — recon, hypothesis generation, exploit testing — against a target you control, and produces a structured report of findings.

> **Authorized testing only.** Fennec is built to assist security testing against systems you own or have explicit written permission to assess. Don't point it at anything else.

## What you get

- **Multi-agent loop**: Recon → Analyst → Pentester → (Coder for exploit dev), coordinated by a pure-routing orchestrator. Built on LangGraph.
- **Local execution**: a Kali Linux container handles the actual tool calls (nmap, curl, sqlmap, gobuster, etc.). Your laptop never runs unverified payloads directly.
- **Provider-agnostic LLMs**: Anthropic, OpenAI, or OpenRouter. Pick one in `.env`.
- **CLI + Dashboard**: a Python CLI for one-shot runs, and an optional React dashboard for live progress + findings.

There's a hosted SaaS version of Fennec with team features, persistent jobs, and a managed runner. This open-source repo is the same agent core, stripped of the multi-tenant infrastructure — designed to run on one laptop with one API key.

## Requirements

- Python 3.11+
- Docker (for the Kali execution container)
- An LLM API key (Anthropic, OpenAI, or OpenRouter)
- Node 18+ (only if you want the dashboard UI)

## Quickstart

```bash
git clone git@github.com:NabilAziz99/Fennec.git
cd Fennec

# 1. Set up env
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY (or OPENAI_API_KEY / OPENROUTER_API_KEY)

# 2. Build the Kali execution image (one-time, ~5 min)
cd linux && make build && cd ..

# 3. Install Python deps
pip install -r requirements.txt

# 4a. Run a scan via CLI
python cli.py scan --target http://localhost:8000 --output ./reports

# 4b. Or start the FastAPI server and use the dashboard
uvicorn src.api.server:app --host 0.0.0.0 --port 8000
# then in another terminal: cd frontend && npm install && npm run dev
```

A CLI report directory under `./reports/<timestamp>_<host>/` will contain `summary.md`, per-agent activity logs, and a `findings/` directory.

### With Docker Compose

```bash
docker compose up --build
```

This boots the FastAPI backend on `:8000` and the dashboard on `:3000` (nginx). Open the dashboard, enter a target URL, and watch the agents work.

### Dashboard

The React dashboard (`frontend/`) talks to the FastAPI server (`src/api/server.py`) over HTTP + SSE. State is in-memory — there is no database — so jobs disappear when the server restarts. Set `VITE_API_BASE_URL` in `frontend/.env` if the API isn't at `http://localhost:8000`.

### Programmatic interface

```python
import asyncio
from agent import run_pentest, PentestTask, PentestMode

async def main():
    task = PentestTask(
        target_url="http://localhost:8000",
        description="Find authentication and injection vulnerabilities",
        mode=PentestMode.BLACK_BOX,
        tags=["sqli", "auth"],
    )
    result = await run_pentest(task)
    print(f"Success: {result.success}")
    for v in result.vulnerabilities:
        print(f"  - {v}")

asyncio.run(main())
```

## Configuration

Everything is driven by `.env`. The important knobs:

| Variable | What it does |
|---|---|
| `LLM_PROVIDER` | `anthropic`, `openai`, or `openrouter` |
| `LLM_MODEL` | Model name for the provider (e.g. `claude-sonnet-4-20250514`) |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `OPENROUTER_API_KEY` | One of these must be set, matching `LLM_PROVIDER` |
| `DOCKER_IMAGE` | Kali image to use (default: `fennec-linux`, built locally) |
| `EXECUTION_MODE` | `docker` (default) or `local` (run tools inside the agent container) |
| `FENNEC_METHOD` | `turbo` (fast), `balanced` (default), or `deep` (slower, more thorough) |
| `HTLI` | `true` to enable Human-In-The-Loop review — pauses for operator approval before testing hypotheses |
| `RECON_MIN_MODEL_CALLS`, `ANALYST_MODEL_CALL_LIMIT`, `PENTESTER_MODEL_CALL_LIMIT` | Per-agent call-budget caps |
| `TAVILY_API_KEY`, `PERPLEXITY_API_KEY` | Optional — enables enhanced web search during recon |
| `LANGSMITH_TRACING` | `true` to send traces to LangSmith (optional) |

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Recon     │ ──> │   Analyst    │ ──> │ Orchestrator │
│ (scan tools)│     │ (hypotheses) │     │  (routing)   │
└─────────────┘     └──────────────┘     └──────┬───────┘
                                                │
                                                ▼
                                         ┌──────────────┐
                                         │  Pentester   │
                                         │  (testing)   │
                                         └──────────────┘
                                                │
                            ┌───────────────────┘
                            ▼
                     ┌─────────────┐
                     │    Coder    │  (invoked by pentester
                     │ (exploits)  │   when custom payload needed)
                     └─────────────┘
```

- **Recon** runs once at the start (and again if the analyst needs more data). It builds a `ReconData` snapshot of the target.
- **Analyst** consumes recon data and emits a queue of testable hypotheses.
- **Pentester** picks the next hypothesis, runs targeted tool calls, and emits a `PentesterResult` (verdict + evidence).
- **Orchestrator** processes pentester results into findings and decides what's next — more testing, more recon, or done.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full breakdown.

## Differences from the hosted version

| | OSS (this repo) | Hosted SaaS |
|---|---|---|
| Auth | None — local single-user | Email/OAuth, team workspaces |
| Job persistence | JSON report files | Postgres-backed history |
| Queue | In-process (one scan at a time) | Pub/Sub + autoscaled workers |
| Dashboard | Local Vite dev server | Hosted, with sharing + collaboration |
| LLM keys | Yours, in `.env` | Managed |
| Updates | `git pull` | Continuous |

The agent code itself is identical between the two — only the surrounding infrastructure differs.

## Project layout

```
.
├── agent.py                  # Programmatic interface — `run_pentest(task)`
├── cli.py / cli/main.py      # CLI entrypoint
├── src/
│   ├── agents/               # recon, analyst, pentester, coder, human_review, emission
│   ├── graph/                # LangGraph wiring
│   ├── tools/                # Tool implementations (terminal, browser, file ops, web search)
│   ├── docker/               # aiodocker wrapper for the Kali container
│   ├── prompts/              # Per-agent system prompts
│   ├── schemas/              # Pydantic schemas for tool I/O
│   ├── state/                # FennecState + hypothesis/finding types
│   ├── middleware/           # LangChain middleware (budget, truncation, retries)
│   └── orchestration/        # HypothesisManager
├── linux/                    # Kali Dockerfile + tools list (`make build` to build image)
├── frontend/                 # React + Vite dashboard (optional)
└── docker-compose.yml
```

## Contributing

Issues and PRs welcome. Before submitting:

- Run `python -m py_compile src/**/*.py` to catch syntax errors.
- If you're adding a new tool or agent, update the corresponding prompt in `src/prompts/`.
- Don't add proprietary services or auth — this repo stays vendor-neutral.

## License

[Apache License 2.0](LICENSE). See `LICENSE` for the full text.

## Acknowledgements

Built on [LangGraph](https://github.com/langchain-ai/langgraph), [LangChain](https://github.com/langchain-ai/langchain), and the [Kali Linux](https://www.kali.org/) tools ecosystem.
