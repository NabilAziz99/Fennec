"""
Hypothesis management tools for agents.

Allows agents to interact with the global hypothesis tree:
- hypothesis_create: Add a new hypothesis to explore
- hypothesis_list: See all hypotheses and their status
- hypothesis_get: Get full details of a hypothesis
- hypothesis_update: Update hypothesis details

These complement the task tools (internal steps) by managing
the global exploration tree.
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional


class HypothesisCreateInput(BaseModel):
    """Input for creating a hypothesis."""
    title: str = Field(
        description="Short title (e.g., 'Test IDOR on /api/users')"
    )
    description: str = Field(
        default="",
        description="Detailed description of what to test and why"
    )
    required_agent: str = Field(
        default="pentester",
        description="Agent type needed: pentester or coder"
    )
    skills: list[str] = Field(
        default_factory=list,
        description="Skills to inject (e.g., ['sql_injection', 'authentication'])"
    )
    priority: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Priority 0.0-1.0, higher = explore sooner"
    )
    expected_outputs: list[str] = Field(
        default_factory=list,
        description="What this hypothesis might produce (e.g., ['admin_session'])"
    )
    blocked_by_output: Optional[str] = Field(
        default=None,
        description="Output name this hypothesis needs (will be blocked until available)"
    )


class HypothesisGetInput(BaseModel):
    """Input for getting a hypothesis."""
    hypothesis_id: str = Field(description="The ID of the hypothesis to retrieve")


class HypothesisUpdateInput(BaseModel):
    """Input for updating a hypothesis."""
    hypothesis_id: str = Field(description="The ID of the hypothesis to update")
    priority: Optional[float] = Field(
        default=None,
        description="New priority (0.0-1.0)"
    )
    add_skills: list[str] = Field(
        default_factory=list,
        description="Skills to add"
    )


@tool(args_schema=HypothesisCreateInput)
def hypothesis_create(
    title: str,
    description: str = "",
    required_agent: str = "pentester",
    skills: list = None,
    priority: float = 0.5,
    expected_outputs: list = None,
    blocked_by_output: str = None,
) -> str:
    """
    Create a new hypothesis to add to the exploration tree.

    Use this when you discover a NEW attack surface or need a
    DIFFERENT agent to handle something.

    DO NOT create hypotheses for things you can handle yourself -
    use task_create for internal steps instead.

    Examples:
        # Found a new endpoint during recon
        hypothesis_create(
            title="Test file upload on /api/upload",
            description="Discovered file upload endpoint, test for unrestricted upload",
            skills=["file_upload", "rce"],
            priority=0.8
        )

        # Need pentester to research CVE info (using web_search)
        hypothesis_create(
            title="Research Apache Struts CVEs",
            description="Server running Struts 2.3.x, find known vulnerabilities",
            required_agent="pentester",
            skills=["cve_research"],
            expected_outputs=["struts_cve_list"]
        )

        # This depends on getting credentials first
        hypothesis_create(
            title="Access admin panel",
            description="Use extracted credentials to access admin",
            blocked_by_output="admin_credentials",
            expected_outputs=["admin_session"]
        )
    """
    blocked_str = f" (blocked until '{blocked_by_output}' available)" if blocked_by_output else ""
    return f"Hypothesis created: {title}{blocked_str}"


@tool
def hypothesis_list() -> str:
    """
    List all hypotheses in the exploration tree.

    Shows:
    - Hypothesis ID and title
    - Status (pending/in_progress/completed/blocked/dead_end)
    - Required agent
    - Whether it's blocked and what it's waiting for

    Use this to understand the current state of the exploration
    and see what other hypotheses exist.
    """
    return "Listing hypotheses..."


@tool(args_schema=HypothesisGetInput)
def hypothesis_get(hypothesis_id: str) -> str:
    """
    Get full details of a specific hypothesis.

    Returns title, description, status, skills, findings,
    task list, and dependency information.
    """
    return f"Getting hypothesis {hypothesis_id}..."


@tool(args_schema=HypothesisUpdateInput)
def hypothesis_update(
    hypothesis_id: str,
    priority: float = None,
    add_skills: list = None,
) -> str:
    """
    Update a hypothesis's priority or skills.

    Use this to:
    - Increase priority of a promising hypothesis
    - Add skills based on what you've learned
    """
    parts = [f"Hypothesis {hypothesis_id} updated"]
    if priority is not None:
        parts.append(f"priority={priority}")
    if add_skills:
        parts.append(f"added skills: {add_skills}")
    return ", ".join(parts)


def get_hypothesis_management_tools():
    """Get the hypothesis management tools for agents."""
    return [hypothesis_create, hypothesis_list, hypothesis_get, hypothesis_update]
