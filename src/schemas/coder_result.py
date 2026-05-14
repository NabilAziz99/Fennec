"""
Structured output schema for the coder agent.
"""

from pydantic import BaseModel, Field


class CoderResult(BaseModel):
    """Structured result from the coder agent — coding task outcome."""
    success: bool = Field(
        description="Whether the coding task succeeded"
    )
    result: str = Field(
        description="Description of what was created or done"
    )
    files_created: list[str] = Field(
        default_factory=list,
        description="List of files created"
    )
    files_modified: list[str] = Field(
        default_factory=list,
        description="List of files modified"
    )
    error: str = Field(
        default="",
        description="Error message if failed"
    )
    code_snippet: str = Field(
        default="",
        description="Key code snippet or summary of generated code"
    )
