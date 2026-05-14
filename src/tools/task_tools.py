"""
Task tools for agents - matches Claude Code's task system.

DEPRECATED: Agents now use TodoListMiddleware (from create_agent middleware)
instead of these manual task tools. This module is kept for backwards
compatibility but should not be used in new agent code.

Four individual tools:
- task_create: Create a new task
- task_update: Update an existing task
- task_get: Get a task by ID
- task_list: List all tasks

Reading is also available PROGRAMMATICALLY (auto-injected into prompt).
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional


# ============ Input Schemas ============

class TaskCreateInput(BaseModel):
    """Input for task_create."""
    subject: str = Field(description="Brief imperative title (e.g., 'Run nmap scan on target')")
    description: str = Field(description="Detailed description of what needs to be done")
    activeForm: str = Field(
        default="",
        description="Present continuous form shown while in progress (e.g., 'Running nmap scan')"
    )


class TaskUpdateInput(BaseModel):
    """Input for task_update."""
    taskId: str = Field(description="The ID of the task to update")
    status: Optional[str] = Field(
        default=None,
        description="New status: 'pending' | 'in_progress' | 'completed'"
    )
    subject: Optional[str] = Field(default=None, description="New subject")
    description: Optional[str] = Field(default=None, description="New description")
    activeForm: Optional[str] = Field(default=None, description="New activeForm")
    owner: Optional[str] = Field(default=None, description="New owner (agent name)")
    metadata: Optional[dict] = Field(
        default=None,
        description="Metadata keys to merge. Set a key to null to delete it."
    )
    addBlocks: Optional[list[str]] = Field(
        default=None,
        description="Task IDs that cannot start until this task completes"
    )
    addBlockedBy: Optional[list[str]] = Field(
        default=None,
        description="Task IDs that must complete before this task can start"
    )


class TaskGetInput(BaseModel):
    """Input for task_get."""
    taskId: str = Field(description="The ID of the task to retrieve")


# ============ Tools ============

@tool(args_schema=TaskCreateInput)
def task_create(subject: str, description: str, activeForm: str = "") -> str:
    """
    Create a new task to track your work.

    Use this when starting multi-step work to make progress visible.
    All tasks are created with status 'pending'.

    The subject should be imperative ("Run tests") and activeForm
    should be present continuous ("Running tests").
    """
    # Actual creation happens in the agent node; tool just validates input
    return f"Task created: {subject}"


@tool(args_schema=TaskUpdateInput)
def task_update(
    taskId: str,
    status: Optional[str] = None,
    subject: Optional[str] = None,
    description: Optional[str] = None,
    activeForm: Optional[str] = None,
    owner: Optional[str] = None,
    metadata: Optional[dict] = None,
    addBlocks: Optional[list[str]] = None,
    addBlockedBy: Optional[list[str]] = None,
) -> str:
    """
    Update an existing task.

    Common uses:
    - Set status to 'in_progress' when starting work on a task
    - Set status to 'completed' when done
    - Add dependencies with addBlocks/addBlockedBy

    IMPORTANT:
    - Only mark completed when work is FULLY done
    - Set to in_progress BEFORE starting work
    """
    # Actual update happens in the agent node
    return f"Task #{taskId} updated"


@tool(args_schema=TaskGetInput)
def task_get(taskId: str) -> str:
    """
    Get full details of a task by ID.

    Returns subject, description, status, owner, blocks, and blockedBy.
    Use this before starting work to understand full requirements.
    """
    # Actual lookup happens in the agent node
    return f"Fetching task #{taskId}"


@tool
def task_list() -> str:
    """
    List all tasks with their status.

    Returns a summary: id, subject, status, owner, blockedBy.
    Use after completing a task to find the next one to work on.
    """
    # Actual listing happens in the agent node
    return "Listing all tasks"


# ============ Exports ============

def get_task_tools():
    """Get all four task tools (Claude Code style)."""
    return [task_create, task_update, task_get, task_list]


# Keep old name for backwards compatibility
get_todo_tools = get_task_tools

# Legacy single-tool reference (points to task_create as closest equivalent)
todo_write = task_create
