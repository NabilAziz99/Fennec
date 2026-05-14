"""Reproduce the silent-None failure of `_extract_recon_result` on a large
message history (the scenario that happened on job fbfc9457).

Invocation: `python3 tests/test_recon_fallback_large_context.py`
Cost: one real LLM call (~cents). Prints the RAW response so we can see
exactly why the schema-bound path returns None.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import textwrap

_THIS = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_THIS)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.config.settings import get_default_llm  # noqa: E402
from src.schemas.recon_result import ReconResult  # noqa: E402


def _bulky_curl_output(n: int) -> str:
    """Simulate a long `curl -v` dump like the real recon tool outputs.
    Pad it out so it matches the ~3–10 KB each call produced in prod
    (JWTs, OpenAPI JSON, gobuster 403-dumps, etc.)."""
    header = textwrap.dedent(f"""
        * Host www.sigmanticai.com:443 was resolved.
        * IPv4: 216.198.79.1
        * TLSv1.3 (OUT), TLS handshake, Client hello (1):
        * TLSv1.3 (IN), TLS handshake, Server hello (2):
        * SSL connection using TLSv1.3 / TLS_AES_128_GCM_SHA256
        * Server certificate: CN=www.sigmanticai.com
        > GET /path-{n} HTTP/2
        > Host: www.sigmanticai.com
        > User-Agent: curl/8.14.1
        > Accept: */*
        < HTTP/2 200
        < server: Vercel
        < content-type: text/html; charset=utf-8
        < cache-control: public, max-age=0, must-revalidate
        < strict-transport-security: max-age=63072000
        < x-vercel-cache: HIT
        < x-vercel-id: pdx1::abc123-def-456
        < content-length: 4567
        <
        <!DOCTYPE html>
        <html lang="en">
        <head><title>Page {n}</title><link rel="stylesheet" href="styles.css">
        <script src="supabase-config.js"></script></head>
        <body>
        <nav><a href="/home">Home</a><a href="/login">Login</a>
        <a href="/pricing">Pricing</a><a href="/docs">Docs</a></nav>
    """).strip()
    # pad with realistic filler (401 body dumps, script tags, etc.) per call
    filler = "\n".join(
        f'<div class="item-{n}-{i}" data-id="{n*100+i}" data-hash="abc{i:04d}def{n:04d}">content block {i} of page {n}</div>'
        for i in range(80)
    )
    return header + "\n" + filler + "\n</body></html>"


def _build_fake_recon_history(tool_call_count: int = 15) -> list:
    """Mimic the message list a recon agent accumulates when it burns budget
    without emitting ReconResult. Each pair is an AIMessage(tool_call) +
    ToolMessage(result)."""
    messages: list = [
        HumanMessage(
            content="Target: https://www.sigmanticai.com/. Enumerate attack surface."
        ),
    ]
    for i in range(tool_call_count):
        tool_id = f"t{i}"
        messages.append(
            AIMessage(
                content="",
                tool_calls=[{
                    "id": tool_id,
                    "name": "terminal",
                    "args": {"command": f"curl -v https://www.sigmanticai.com/path{i}"},
                }],
            )
        )
        messages.append(
            ToolMessage(
                tool_call_id=tool_id,
                name="terminal",
                content=_bulky_curl_output(i),
            )
        )
    # Final "please emit" instruction like FinalizeBeforeModelLimitMiddleware does
    messages.append(
        HumanMessage(
            content=(
                "## FINALIZE (BUDGET)\n"
                "You are about to hit the model-call limit. Do NOT call any "
                "regular tools. Return the final structured response NOW using "
                "the ReconResult tool. Summarize ALL findings."
            )
        )
    )
    return messages


async def run() -> int:
    if not any(os.getenv(k) for k in ("OPENROUTER_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY")):
        print("SKIP: no LLM API keys in env")
        return 0

    llm = get_default_llm()
    print(f"[config] llm class = {type(llm).__name__}")
    model_name = getattr(llm, "model_name", None) or getattr(llm, "model", "?")
    print(f"[config] model = {model_name}")

    messages = _build_fake_recon_history(tool_call_count=15)
    # Inject the REAL recon system prompt + fake credentials — mirrors prod
    from src.agents.recon import get_recon_prompt
    real_sys = get_recon_prompt(
        target_url="https://www.sigmanticai.com/",
        task_description="Identify and exploit vulnerabilities",
        auth_credentials={
            "username": "aziztaleb@sigmanticai.com",
            "password": "fake-test-password-not-real",
            "auth_type": "form",
        },
    )
    messages = [SystemMessage(content=real_sys), *messages]
    total_chars = sum(len(str(m.content)) for m in messages)
    print(f"[input] messages={len(messages)} total_chars={total_chars:,} sys_prompt_chars={len(real_sys):,}")

    # Bind with include_raw so we can see what the LLM actually returned
    extractor = llm.with_structured_output(
        ReconResult,
        method="function_calling",
        include_raw=True,
    )
    sys_msg = SystemMessage(content=(
        "You are a reconnaissance analyst. The preceding messages contain tool "
        "outputs. Produce a ReconResult summarizing everything observed."
    ))
    trigger = HumanMessage(content="Now produce the ReconResult structured output.")

    print("\n[invoking] llm.with_structured_output(method='function_calling', include_raw=True).ainvoke(...)")
    result = await extractor.ainvoke([sys_msg, *messages, trigger])

    raw = result.get("raw") if isinstance(result, dict) else None
    parsed = result.get("parsed") if isinstance(result, dict) else None
    err = result.get("parsing_error") if isinstance(result, dict) else None

    print("\n=== RAW LLM RESPONSE ===")
    if raw is None:
        print("raw is None")
    else:
        print("type(raw):", type(raw).__name__)
        # content
        content = getattr(raw, "content", "")
        print("raw.content type:", type(content).__name__)
        if isinstance(content, str):
            print(f"raw.content (text, {len(content)} chars):")
            print(textwrap.indent(content[:2000], "  "))
            if len(content) > 2000:
                print(f"  ... ({len(content)-2000} more chars)")
        else:
            print("raw.content (non-string):", str(content)[:500])
        # tool calls
        tcs = getattr(raw, "tool_calls", None) or []
        print(f"raw.tool_calls: {len(tcs)}")
        for i, tc in enumerate(tcs):
            name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", "?")
            args = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {})
            print(f"  [{i}] name={name} args_keys={list(args.keys()) if isinstance(args,dict) else '?'}")
        # finish reason, response metadata
        meta = getattr(raw, "response_metadata", {}) or {}
        print("raw.response_metadata keys:", list(meta.keys())[:10])
        print("finish_reason:", meta.get("finish_reason"))

    print("\n=== PARSED ===")
    print("type(parsed):", type(parsed).__name__ if parsed is not None else "None")
    if parsed is not None:
        print(" summary:", (parsed.summary or "")[:80])
        print(" endpoints:", len(parsed.endpoints))
        print(" technologies:", len(parsed.technologies))

    print("\n=== parsing_error ===")
    print(err)

    print("\n=== VERDICT ===")
    if parsed is None and raw is not None and not getattr(raw, "tool_calls", None):
        print("DIAGNOSIS: LLM returned plain text instead of calling the ReconResult tool.")
        print("This is why extractor.ainvoke returned None — no tool call to parse.")
        return 2
    elif parsed is None and raw is not None and getattr(raw, "tool_calls", None):
        print("DIAGNOSIS: Tool was called but Pydantic validation failed (parsing_error above).")
        return 3
    elif parsed is not None:
        print("PASS: extraction returned a valid ReconResult.")
        return 0
    else:
        print("UNKNOWN: no parsed result and no raw.")
        return 4


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
