"""
Budget-aware prompt middleware for LangChain v1 agents.

At each model call, injects a one-line budget-status message into the system
prompt so the LLM can self-regulate rather than being hard-cut off.
"""

from __future__ import annotations

import logging
from typing import Awaitable, Callable

from langchain_core.messages import SystemMessage

logger = logging.getLogger(__name__)
from langchain.agents.middleware.types import (
    AgentMiddleware,
    ModelRequest,
    ModelResponse,
    ModelCallResult,
)

MAX_TOOL_CALLS = 8  # default; callers should pass run_limit explicitly


class BudgetAwarePromptMiddleware(AgentMiddleware):
    """Inject a remaining-budget hint into the system prompt each model call."""

    def __init__(self, *, run_limit: int = MAX_TOOL_CALLS) -> None:
        super().__init__()
        self.run_limit = run_limit

    # ------------------------------------------------------------------
    # Middleware hooks
    # ------------------------------------------------------------------

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        return handler(self._inject(request))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelCallResult:
        return await handler(self._inject(request))

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _inject(self, request: ModelRequest) -> ModelRequest:
        count = int(request.state.get("run_model_call_count", 0) or 0)
        remaining = self.run_limit - count

        # Skip on the very first call — no budget info to share yet
        if count == 0:
            logger.info("budget_aware_prompt: call 0, skipping injection (limit=%d)", self.run_limit)
            return request

        prompt = f"[Budget] {remaining}/{self.run_limit} model calls remaining."

        if remaining <= 2:
            level = "critical"
            prompt += (
                " You are nearly out of steps —"
                " stop gathering information and synthesize your best answer now."
            )
        elif remaining <= self.run_limit // 2:
            level = "warning"
            prompt += (
                " You are halfway through your budget —"
                " avoid redundant tool calls and focus on what matters most."
            )
        else:
            level = "ok"
            prompt += " Use your steps deliberately; stop as soon as you can answer confidently."

        logger.info(
            "budget_aware_prompt: call=%d remaining=%d/%d level=%s",
            count, remaining, self.run_limit, level,
        )

        if request.system_message is not None:
            new_blocks = [
                *request.system_message.content_blocks,
                {"type": "text", "text": prompt},
            ]
            new_system = SystemMessage(content=new_blocks)
        else:
            new_system = SystemMessage(content=prompt)

        return request.override(system_message=new_system)
