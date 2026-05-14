"""
Truncate-old-tool-outputs middleware for LangChain v1 agents.

Before each model call, if the message history is large, replaces the CONTENT of
older ``ToolMessage`` entries with a short stub so the prompt stays inside the
model's practical context limits. The stub preserves ``tool_call_id`` and
``name`` fields so the Anthropic API's tool_use/tool_result pairing rule is
respected — we never *remove* a ToolMessage, we only shrink its content.

Why this exists
---------------
Per-agent message histories accumulate verbose tool output (e.g. ``curl -v``
TLS handshakes, full dirsearch output). When one agent hands off to another
(recon → analyst → pentester), the next agent inherits the full chain and
can blow past the provider's context limit, causing the LLM to return an
empty response (observed in production: pentester silently dies, no
structured output produced).

Strategy
--------
1. Walk the messages list.
2. Keep the last ``KEEP_RECENT_TOOL_MESSAGES`` ToolMessages unchanged
   (except content is capped at ``MAX_CHARS_PER_KEPT_OUTPUT`` to avoid a
   single monster output blowing everything up).
3. For older ToolMessages, replace ``content`` with a short stub that
   references the original tool name and the args the model used, so the
   model still knows what it called and roughly what came back.
4. Only run the compaction when total character count across all messages
   exceeds ``TRIGGER_TOTAL_CHARS`` — small prompts are left untouched.

The middleware never touches ``HumanMessage`` / ``AIMessage`` / ``SystemMessage``
content, so the model's reasoning chain is preserved.
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from langchain_core.messages import AIMessage, ToolMessage
from langchain.agents.middleware.types import (
    AgentMiddleware,
    ModelRequest,
    ModelResponse,
    ModelCallResult,
)

logger = logging.getLogger(__name__)


# ---- Tunable knobs -----------------------------------------------------------

# Keep the last N ToolMessages in full (subject to per-output cap below).
DEFAULT_KEEP_RECENT = 6

# Cap size of any kept ToolMessage content (chars). Longer outputs get tail-clipped.
DEFAULT_MAX_CHARS_PER_KEPT = 4_000

# Only run compaction when the total chars across all messages exceeds this.
DEFAULT_TRIGGER_TOTAL_CHARS = 60_000

# Max length for the args preview embedded in the stub message.
ARGS_PREVIEW_CHARS = 200


class TruncateOldToolOutputsMiddleware(AgentMiddleware):
    """Compact old ToolMessage contents to fit the context window.

    Emits one structured log line per model call so compression events
    are easy to grep per agent / per job. Example:

        [truncate_tool_outputs agent=recon] compacted=3/9 saved_chars=24180 \
          total=98421->74241 (threshold=60000) kept_recent=6 max_per_kept=4000

    The per-run totals (`_stats`) survive inside this middleware instance,
    so callers can log a summary at end of run via ``get_stats()``.
    """

    def __init__(
        self,
        *,
        agent_name: str = "",
        keep_recent: int = DEFAULT_KEEP_RECENT,
        max_chars_per_kept: int = DEFAULT_MAX_CHARS_PER_KEPT,
        trigger_total_chars: int = DEFAULT_TRIGGER_TOTAL_CHARS,
    ) -> None:
        super().__init__()
        self.agent_name = agent_name or ""
        self.keep_recent = max(0, int(keep_recent))
        self.max_chars_per_kept = max(500, int(max_chars_per_kept))
        self.trigger_total_chars = max(1_000, int(trigger_total_chars))
        self._stats = {
            "calls_seen": 0,
            "calls_compacted": 0,
            "tool_messages_compacted": 0,
            "chars_saved_total": 0,
        }
        # Attach-time log line so we can confirm from production logs that
        # the middleware is actually wired into each agent's create_agent()
        # call — after a run where none of the compaction log lines showed
        # up we had no way to tell whether (a) the middleware wasn't firing
        # or (b) the threshold was never hit. This line fires once per
        # agent per invocation at construction time.
        logger.info(
            "%s attached (trigger_total_chars=%d keep_recent=%d max_chars_per_kept=%d)",
            self._log_prefix(),
            self.trigger_total_chars,
            self.keep_recent,
            self.max_chars_per_kept,
        )

    def get_stats(self) -> dict:
        """Return a copy of aggregated compression stats for this run."""
        return dict(self._stats)

    def _log_prefix(self) -> str:
        return (
            f"[truncate_tool_outputs agent={self.agent_name}]"
            if self.agent_name
            else "[truncate_tool_outputs]"
        )

    # ------------------------------------------------------------------
    # Middleware hooks
    # ------------------------------------------------------------------

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        return handler(self._maybe_truncate(request))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelCallResult:
        return await handler(self._maybe_truncate(request))

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def _maybe_truncate(self, request: ModelRequest) -> ModelRequest:
        messages = getattr(request, "messages", None)
        if not messages:
            return request

        self._stats["calls_seen"] += 1

        total = sum(len(_content_str(m)) for m in messages)
        if total < self.trigger_total_chars:
            logger.debug(
                "%s below_trigger total=%d threshold=%d — skipping",
                self._log_prefix(),
                total,
                self.trigger_total_chars,
            )
            return request

        tool_indices = [i for i, m in enumerate(messages) if isinstance(m, ToolMessage)]
        if len(tool_indices) <= self.keep_recent:
            # Nothing old to compact. Still cap any kept outputs.
            new_messages = [self._cap_if_tool(m) for m in messages]
            new_total = sum(len(_content_str(m)) for m in new_messages)
            if new_total != total:
                self._stats["calls_compacted"] += 1
                self._stats["chars_saved_total"] += total - new_total
                logger.info(
                    "%s cap_only kept=%d/%d total=%d->%d (threshold=%d)",
                    self._log_prefix(),
                    len(tool_indices),
                    len(tool_indices),
                    total,
                    new_total,
                    self.trigger_total_chars,
                    extra={
                        "agent": self.agent_name,
                        "event": "truncate_tool_outputs.cap_only",
                        "kept": len(tool_indices),
                        "compacted": 0,
                        "chars_before": total,
                        "chars_after": new_total,
                        "threshold": self.trigger_total_chars,
                    },
                )
            return self._override_if_changed(request, messages, new_messages)

        to_compact = set(tool_indices[: -self.keep_recent] if self.keep_recent > 0 else tool_indices)

        # Build lookup: tool_call_id -> (tool_name, args_dict) from AI messages
        call_args_by_id: dict[str, tuple[str, Any]] = {}
        for m in messages:
            if isinstance(m, AIMessage):
                for tc in (getattr(m, "tool_calls", None) or []):
                    tc_id = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
                    tc_name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
                    tc_args = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", None)
                    if tc_id:
                        call_args_by_id[tc_id] = (tc_name or "unknown", tc_args or {})

        compacted = 0
        compacted_chars = 0
        new_messages: list = []
        for i, m in enumerate(messages):
            if i in to_compact and isinstance(m, ToolMessage):
                orig = _content_str(m)
                name, args = call_args_by_id.get(m.tool_call_id, ("unknown", {}))
                args_preview = _format_args(args)[:ARGS_PREVIEW_CHARS]
                stub = (
                    f"[truncated for context — tool={name} "
                    f"orig_size={len(orig)} chars, "
                    f"args={args_preview}]"
                )
                new_messages.append(
                    ToolMessage(
                        content=stub,
                        tool_call_id=m.tool_call_id,
                        name=m.name,
                    )
                )
                compacted += 1
                compacted_chars += len(orig) - len(stub)
            else:
                new_messages.append(self._cap_if_tool(m))

        new_total = sum(len(_content_str(m)) for m in new_messages)
        self._stats["calls_compacted"] += 1
        self._stats["tool_messages_compacted"] += compacted
        self._stats["chars_saved_total"] += total - new_total
        logger.info(
            "%s compacted=%d/%d tool_msgs saved=%d chars total=%d->%d (threshold=%d)",
            self._log_prefix(),
            compacted,
            len(tool_indices),
            compacted_chars,
            total,
            new_total,
            self.trigger_total_chars,
            extra={
                "agent": self.agent_name,
                "event": "truncate_tool_outputs.compact",
                "compacted": compacted,
                "tool_messages_total": len(tool_indices),
                "chars_saved_direct": compacted_chars,
                "chars_before": total,
                "chars_after": new_total,
                "threshold": self.trigger_total_chars,
                "keep_recent": self.keep_recent,
                "max_chars_per_kept": self.max_chars_per_kept,
            },
        )
        if new_total >= self.trigger_total_chars:
            # Compaction didn't bring us under the threshold — worth flagging
            # because the next call may hit provider context limits.
            logger.warning(
                "%s still_over_threshold after_compact total=%d threshold=%d "
                "(compacted %d/%d messages); consider lowering trigger or "
                "max_chars_per_kept",
                self._log_prefix(),
                new_total,
                self.trigger_total_chars,
                compacted,
                len(tool_indices),
                extra={
                    "agent": self.agent_name,
                    "event": "truncate_tool_outputs.still_over_threshold",
                    "chars_after": new_total,
                    "threshold": self.trigger_total_chars,
                },
            )

        return self._override_if_changed(request, messages, new_messages)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _cap_if_tool(self, m: Any) -> Any:
        """Cap a 'kept' ToolMessage to max_chars_per_kept, tail-clipping overflow."""
        if not isinstance(m, ToolMessage):
            return m
        content = _content_str(m)
        if len(content) <= self.max_chars_per_kept:
            return m
        clipped = content[: self.max_chars_per_kept]
        overflow = len(content) - self.max_chars_per_kept
        clipped += f"\n...[+{overflow} chars truncated]"
        return ToolMessage(
            content=clipped,
            tool_call_id=m.tool_call_id,
            name=m.name,
        )

    def _override_if_changed(
        self, request: ModelRequest, old_messages: list, new_messages: list
    ) -> ModelRequest:
        # Only call override if we actually changed something — avoids unnecessary clones.
        if old_messages is new_messages:
            return request
        if all(a is b for a, b in zip(old_messages, new_messages)):
            return request
        try:
            return request.override(messages=new_messages)
        except Exception:
            # Fallback: some ModelRequest implementations may not accept `messages`
            # in override(). Log and pass through unchanged rather than crash.
            logger.exception(
                "truncate_tool_outputs: request.override(messages=...) not supported; "
                "falling through without truncation"
            )
            return request


# ---- Helpers (module level) --------------------------------------------------


def _content_str(m: Any) -> str:
    content = getattr(m, "content", "")
    if isinstance(content, str):
        return content
    # Some providers use list-of-blocks content
    try:
        return "".join(
            b.get("text", "") if isinstance(b, dict) else str(b) for b in content
        )
    except Exception:
        return str(content)


def _format_args(args: Any) -> str:
    if isinstance(args, dict):
        # Prefer common fields so the stub is informative
        for key in ("command", "url", "query", "path", "host", "target"):
            if key in args and args[key]:
                return f"{key}={args[key]!s}"
        return str(args)
    return str(args)
