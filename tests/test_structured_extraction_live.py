"""Live test: `with_structured_output(method="function_calling")` works
against the configured LLM provider (OpenRouter in our current setup).

Run: `python3 -m pytest tests/test_structured_extraction_live.py -s`
or   `python3 tests/test_structured_extraction_live.py`

Costs ~1 real LLM call per schema (cheap). Skips if OPENROUTER_API_KEY or
ANTHROPIC_API_KEY is not set — CI-safe.
"""

from __future__ import annotations

import asyncio
import os
import sys

# Make src importable when running standalone
_THIS = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_THIS)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.config.settings import get_default_llm as get_llm  # noqa: E402
from src.schemas.pentester_result import PentesterResult  # noqa: E402
from src.schemas.recon_result import ReconResult  # noqa: E402


def _have_keys() -> bool:
    return any(
        os.getenv(k)
        for k in ("OPENROUTER_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY")
    )


FAKE_RECON_MESSAGES = [
    HumanMessage(content="Target: http://demo.test/. Enumerate it."),
    AIMessage(
        content="",
        tool_calls=[{"id": "t1", "name": "terminal", "args": {"command": "curl -s http://demo.test/"}}],
    ),
    ToolMessage(
        tool_call_id="t1",
        name="terminal",
        content="HTTP/1.1 200 OK\nServer: Apache/2.4.49\nContent-Type: text/html\n\n<html><body>It works!</body></html>",
    ),
    AIMessage(
        content="",
        tool_calls=[{"id": "t2", "name": "terminal", "args": {"command": "curl -s http://demo.test/login"}}],
    ),
    ToolMessage(
        tool_call_id="t2",
        name="terminal",
        content="HTTP/1.1 200 OK\n\n<form action='/login' method='POST'><input name='email'/><input name='password' type='password'/></form>",
    ),
]


FAKE_PENTESTER_MESSAGES = [
    HumanMessage(content="Hypothesis: test /admin is IDOR-accessible with a regular user token."),
    AIMessage(
        content="",
        tool_calls=[{"id": "p1", "name": "terminal", "args": {"command": "curl -H 'Authorization: Bearer alice' http://demo.test/api/admin/users/2"}}],
    ),
    ToolMessage(
        tool_call_id="p1",
        name="terminal",
        content='HTTP/1.1 200 OK\nContent-Type: application/json\n\n{"id":2,"email":"bob@demo.test","role":"admin"}',
    ),
]


async def run() -> int:
    if not _have_keys():
        print("SKIP: no LLM API keys in env")
        return 0

    llm = get_llm()
    print(f"[config] llm class = {type(llm).__name__}")

    # --- ReconResult extraction -------------------------------------------
    recon_extractor = llm.with_structured_output(ReconResult, method="function_calling")
    print("[recon] invoking extractor with fake message history...")
    recon_sys = SystemMessage(
        content="Produce a ReconResult summarising the messages. Do NOT invent data."
    )
    recon = await recon_extractor.ainvoke(
        [recon_sys, *FAKE_RECON_MESSAGES, HumanMessage(content="Now emit the ReconResult.")]
    )
    assert isinstance(recon, ReconResult), f"expected ReconResult, got {type(recon)}"
    summary_preview = (recon.summary or "")[:60]
    print(
        f"[recon] OK — techs={len(recon.technologies)} endpoints={len(recon.endpoints)} "
        f"summary='{summary_preview}...'"
    )

    # --- PentesterResult extraction ---------------------------------------
    pent_extractor = llm.with_structured_output(PentesterResult, method="function_calling")
    print("[pentester] invoking extractor with fake exploit trace...")
    pent_sys = SystemMessage(
        content="Produce a PentesterResult. status='completed', verdict based on evidence."
    )
    pent = await pent_extractor.ainvoke(
        [pent_sys, *FAKE_PENTESTER_MESSAGES, HumanMessage(content="Now emit the PentesterResult.")]
    )
    assert isinstance(pent, PentesterResult), f"expected PentesterResult, got {type(pent)}"
    print(f"[pentester] OK — status={pent.status!r} verdict={pent.verdict!r} evidence={len(pent.evidence)}")

    print("\nALL PASS — with_structured_output(method='function_calling') works end-to-end.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
