"""
Coder Agent - Writes exploits, scripts, and tools.

Uses LangChain's create_agent with:
1. Explicit tool list (terminal, file_read, file_write — execution only)
2. Built-in middleware (ToolRetryMiddleware, TodoListMiddleware, ModelCallLimitMiddleware)
3. Structured output via ToolStrategy(CoderResult) — all results in one response

Called by Pentester when custom code is needed (via run_coder).
"""

import logging
from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    TodoListMiddleware,
    ToolRetryMiddleware,
)

try:
    from ..middleware.budget_aware_prompt import BudgetAwarePromptMiddleware
    from ..middleware.finalizeBeforeModelLimitMiddleware import FinalizeBeforeModelLimitMiddleware
    from ..middleware.truncate_tool_outputs import TruncateOldToolOutputsMiddleware
except ImportError:
    from src.middleware.budget_aware_prompt import BudgetAwarePromptMiddleware
    from src.middleware.finalizeBeforeModelLimitMiddleware import FinalizeBeforeModelLimitMiddleware
    from src.middleware.truncate_tool_outputs import TruncateOldToolOutputsMiddleware

try:
    from ..schemas.coder_result import CoderResult
    from ..tools.execution import (
        create_terminal_tool,
        create_file_read_tool,
        create_file_write_tool,
    )
    from ..cli import print_agent_header
except ImportError:
    from src.schemas.coder_result import CoderResult
    from src.tools.execution import (
        create_terminal_tool,
        create_file_read_tool,
        create_file_write_tool,
    )
    from src.cli import print_agent_header

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

CODER_PROMPT = """# CODE DEVELOPMENT SPECIALIST

You are an expert developer focused on security tools and exploit development.

## CAPABILITIES
- Multi-language development (Python, Go, C, Bash, JavaScript)
- Exploit modification and customization
- Security tool development
- Automation scripts and payload generation
- Code analysis and debugging

## TASK
{task}

## CONTEXT
{context}

## TOOLS AVAILABLE
- `terminal` - Run commands (compile, test, execute)
- `file_read` - Read existing files
- `file_write` - Write/create files

## HOW TO REPORT
Do NOT make a separate tool call for every file.
Instead, write all code using terminal/file_write, test it, then produce ONE
structured response at the end containing the result summary, files created,
files modified, and any errors.

## RULES
- Write clean, working code
- Test your code before marking complete
- Handle errors gracefully
- Document dependencies if needed
- Produce your final structured response when done

## BEGIN CODING
Complete the task. Produce your final structured response when finished."""


def get_coder_prompt(task: str, context: str = "") -> str:
    """Generate the coder agent prompt."""
    return CODER_PROMPT.format(
        task=task or "No specific task provided",
        context=context or "No additional context",
    )


# ---------------------------------------------------------------------------
# Runner (called by pentester or directly)
# ---------------------------------------------------------------------------

async def run_coder(
    llm,
    task: str,
    context: str = "",
    config: RunnableConfig = None,
    max_iterations: int = 25,
) -> dict[str, Any]:
    """
    Run the coder agent to complete a coding task.

    Called by the pentester when it needs custom code.
    Uses create_agent with ToolStrategy(CoderResult).

    Args:
        llm: Language model
        task: What code to write
        context: Additional context from pentester
        config: Runnable config (for tool execution)
        max_iterations: Max LLM calls

    Returns:
        Dict with result, files_created, files_modified, success, error, messages
    """
    print_agent_header("coder")

    system_prompt = get_coder_prompt(task, context)

    # ---- tools (execution only) ----
    terminal = create_terminal_tool()
    file_read = create_file_read_tool()
    file_write = create_file_write_tool()

    tools = [terminal, file_read, file_write]

    # ---- build agent ----
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        middleware=[
            ToolRetryMiddleware(max_retries=2, on_failure="continue"),
            TodoListMiddleware(),
            TruncateOldToolOutputsMiddleware(agent_name="coder"),
            BudgetAwarePromptMiddleware(run_limit=max_iterations),
            FinalizeBeforeModelLimitMiddleware(run_limit=max_iterations, buffer=3, structured_tool_name="CoderResult"),
            ModelCallLimitMiddleware(run_limit=max_iterations, exit_behavior="end"),
        ],
        response_format=ToolStrategy(CoderResult),
        name="coder",
    )

    # ---- invoke (fresh messages) ----
    try:
        result = await agent.ainvoke(
            {"messages": []},
            config=config or {},
        )
    except Exception as exc:
        logger.warning("Coder agent invocation error (likely model-call limit): %s", exc)
        result = {"messages": [], "structured_response": None}

    # ---- extract structured response ----
    structured: CoderResult | None = result.get("structured_response")
    if structured is not None:
        return {
            "result": structured.result,
            "files_created": structured.files_created,
            "files_modified": structured.files_modified,
            "success": structured.success,
            "error": structured.error,
            "messages": result["messages"],
        }

    # No structured response (hit iteration limit)
    return {
        "result": "Coder did not complete task",
        "files_created": [],
        "files_modified": [],
        "success": False,
        "error": f"Max iterations ({max_iterations}) reached or no structured response",
        "messages": result["messages"],
    }

