"""
Pydantic schemas for agent delegation and task management.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class DelegateInput(BaseModel):
    """Input for delegating to a specialist agent."""
    task: str = Field(
        description="Detailed task description with all necessary context"
    )
    context: str = Field(
        default="",
        description="Additional context, findings, or constraints"
    )


class SubtaskItem(BaseModel):
    """A single subtask in the plan."""
    title: str = Field(
        description="Short descriptive title"
    )
    description: str = Field(
        description="Detailed description of what needs to be done"
    )
    assigned_agent: Literal["pentester", "coder"] = Field(
        description="Which agent should handle this task"
    )


class SubtaskListInput(BaseModel):
    """Input for creating a task plan."""
    subtasks: list[SubtaskItem] = Field(
        description="List of subtasks to execute"
    )


class SubtaskUpdateInput(BaseModel):
    """Input for updating subtask status."""
    subtask_index: int = Field(
        description="Index of the subtask (0-based)"
    )
    status: Literal["pending", "running", "completed", "failed", "skipped"] = Field(
        description="New status for the subtask"
    )
    result: str = Field(
        default="",
        description="Result or notes for this subtask"
    )


class AskUserInput(BaseModel):
    """Input for asking the user a question."""
    question: str = Field(
        description="The question to ask the user"
    )
    options: Optional[list[str]] = Field(
        default=None,
        description="Optional list of choices for the user"
    )
