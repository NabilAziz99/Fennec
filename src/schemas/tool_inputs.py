"""
Pydantic schemas for tool inputs.
"""

from typing import Literal
from pydantic import BaseModel, Field, field_validator


class TerminalInput(BaseModel):
    """Input schema for terminal command execution."""
    command: str = Field(
        description="The shell command to execute in the Docker container"
    )
    working_dir: str = Field(
        default="/work",
        description="Working directory for command execution"
    )
    timeout: int = Field(
        default=300,
        description="Command timeout in seconds (max 600)",
        ge=1,
    )
    message: str = Field(
        default="",
        description="Brief description of what this command does"
    )

    @field_validator("timeout", mode="before")
    @classmethod
    def clamp_timeout(cls, v: int) -> int:
        """Accept millisecond values from confused LLMs and convert them to seconds."""
        v = int(v)
        if v > 600:
            # Likely passed in milliseconds — convert and clamp
            v = min(v // 1000, 600)
        return max(1, v)


class FileReadInput(BaseModel):
    """Input schema for reading files."""
    path: str = Field(
        description="Absolute path to the file in the container"
    )
    message: str = Field(
        default="",
        description="Brief description of why reading this file"
    )


class FileWriteInput(BaseModel):
    """Input schema for writing files."""
    path: str = Field(
        description="Absolute path where to write the file"
    )
    content: str = Field(
        description="Content to write to the file"
    )
    message: str = Field(
        default="",
        description="Brief description of what this file is for"
    )


class BrowserInput(BaseModel):
    """Input schema for web browser/scraping."""
    url: str = Field(
        description="URL to fetch"
    )
    action: Literal["markdown", "html", "links", "text"] = Field(
        default="markdown",
        description="What to extract: markdown (cleaned content), html (raw), links (all URLs), text (plain text)"
    )
    message: str = Field(
        default="",
        description="Brief description of what you're looking for"
    )


class WebSearchInput(BaseModel):
    """Input schema for web search."""
    query: str = Field(
        description="Search query (e.g. CVE details, exploit techniques, tool usage)"
    )
    max_results: int = Field(
        default=5,
        description="Maximum number of results to return",
        ge=1,
        le=10
    )
    message: str = Field(
        default="",
        description="Brief description of what you're searching for"
    )


