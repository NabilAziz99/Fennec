# Changelog

All notable changes to Fennec will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] - Initial public release

### Added
- Multi-agent pentest loop: Recon → Analyst → Pentester → Coder, with a pure-routing Orchestrator
- CLI entrypoint (`python cli.py --target URL`)
- Programmatic interface (`agent.run_pentest(task)`)
- FastAPI server (`src/api/server.py`) exposing scan lifecycle, job state, SSE event stream, target/credential CRUD, dashboard aggregations
- React + Vite dashboard (`frontend/`) — talks to the FastAPI server over HTTP + SSE
- Kali Linux execution container (built locally via `linux/Dockerfile`)
- Provider-agnostic LLM config (Anthropic, OpenAI, OpenRouter)
- Human-In-The-Loop (HTLI) mode for operator approval gates
- Per-method presets: `turbo`, `balanced`, `deep`
- JSON + Markdown report generation under `./reports/<timestamp>_<host>/`
- Optional Tavily / Perplexity integration for enhanced recon search
