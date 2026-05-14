"""
Finalize-before-limit middleware for LangChain v1 agents.

When the model-call budget is almost exhausted, this middleware disables tool calls
and injects a system instruction to return the final structured output immediately.

NOTE: The structured output tool (e.g. ReconResult) is NOT in ``request.tools`` —
it's added separately by LangChain's ``_get_bound_model()`` via ToolStrategy.
So we strip ALL regular tools from ``request.tools`` to force the LLM to use
only the structured output tool.  We do NOT set ``tool_choice`` because the
ToolStrategy already forces ``tool_choice="any"`` downstream.
"""

from __future__ import annotations

import logging
from typing import Awaitable, Callable

from langchain_core.messages import SystemMessage
from langchain.agents.middleware.types import (
    AgentMiddleware,
    ModelRequest,
    ModelResponse,
    ModelCallResult,
)

logger = logging.getLogger(__name__)


class FinalizeBeforeModelLimitMiddleware(AgentMiddleware):
    """Force finalization before the ModelCallLimitMiddleware hard-stop."""

    def __init__(self, *, run_limit: int, buffer: int = 3, structured_tool_name: str = "") -> None:
        super().__init__()
        self.run_limit = run_limit
        self.buffer = buffer
        self.structured_tool_name = structured_tool_name

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        request = self._maybe_finalize(request)
        return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelCallResult:
        request = self._maybe_finalize(request)
        return await handler(request)

    def _maybe_finalize(self, request: ModelRequest) -> ModelRequest:
        count = int(request.state.get("run_model_call_count", 0) or 0)
        remaining = self.run_limit - count

        if remaining > self.buffer:
            return request

        logger.info(
            "finalize_middleware: call=%d remaining=%d/%d — injecting finalization",
            count, remaining, self.run_limit,
        )

        finalize_text = (
            "\n\n## FINALIZE (BUDGET)\n"
            "You are about to hit the model-call limit.\n"
            "- Do NOT call any regular tools (terminal, browser, web_search, etc.).\n"
            "- Return the final structured response NOW using the structured output tool.\n"
            "- Summarize ALL your findings so far into the structured response.\n"
        )

        if request.system_message is not None:
            new_blocks = [
                *request.system_message.content_blocks,
                {"type": "text", "text": finalize_text},
            ]
            new_system = SystemMessage(content=new_blocks)
        else:
            new_system = SystemMessage(content=finalize_text)

        # Remove ALL regular tools so the LLM can only use the structured output
        # tool (which is added back by the framework's ToolStrategy binding).
        return request.override(
            system_message=new_system,
            tools=[],
        )
