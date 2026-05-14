"""
Tools available to the recon agent.
"""

from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field
from typing import Optional

try:
    from .execution import create_terminal_tool, create_browser_tool
    from .task_tools import get_task_tools
except ImportError:
    from src.tools.execution import create_terminal_tool, create_browser_tool
    from src.tools.task_tools import get_task_tools


# === Schemas ===

class AddEndpointInput(BaseModel):
    """Input for adding an endpoint."""
    path: str = Field(description="The endpoint path (e.g., /api/users)")
    method: str = Field(default="GET", description="HTTP method")
    parameters: list[str] = Field(default_factory=list, description="Query or body parameters")
    auth_required: bool = Field(default=False, description="Whether auth is required")
    response_type: str = Field(default="", description="Response type (json, html, etc.)")
    notes: str = Field(default="", description="Additional notes")


class AddTechnologyInput(BaseModel):
    """Input for adding a technology."""
    name: str = Field(description="Technology name (e.g., Express, React)")
    version: Optional[str] = Field(default=None, description="Version if known")
    type: str = Field(default="other", description="Type: framework, language, database, server, cms, library, auth, other")
    confidence: float = Field(default=0.5, description="Confidence level 0.0-1.0")


class AddEntryPointInput(BaseModel):
    """Input for adding an entry point."""
    location: str = Field(description="Location (URL path or parameter)")
    type: str = Field(description="Type: form, api, header, cookie, file_upload, query_param, etc.")
    input_type: str = Field(default="", description="Input type: text, number, file, etc.")
    validation_observed: str = Field(default="", description="What validation was observed")
    notes: str = Field(default="", description="Additional notes")


class SetAuthInfoInput(BaseModel):
    """Input for setting authentication info."""
    auth_type: str = Field(description="Auth type: jwt, session, basic, oauth, api_key, none")
    login_endpoint: Optional[str] = Field(default=None, description="Login endpoint if found")
    registration_available: bool = Field(default=False, description="Whether registration is available")


class AddNoteInput(BaseModel):
    """Input for adding a note."""
    note: str = Field(description="Observation or note to record")


class ReconCompleteInput(BaseModel):
    """Input for completing recon."""
    summary: str = Field(description="Brief summary of findings")
    priority_targets: list[str] = Field(default_factory=list, description="Priority targets for testing")


# === Tool Functions ===

def get_recon_tools(config: RunnableConfig):
    """Get tools for the recon agent."""

    # Execution tools
    terminal = create_terminal_tool()
    browser = create_browser_tool()

    # Data recording tools
    @tool(args_schema=AddEndpointInput)
    def add_endpoint(
        path: str,
        method: str = "GET",
        parameters: list = None,
        auth_required: bool = False,
        response_type: str = "",
        notes: str = "",
    ) -> str:
        """
        Record a discovered endpoint.

        Call this for each endpoint/route you discover during recon.
        """
        return f"Endpoint recorded: {method} {path}"

    @tool(args_schema=AddTechnologyInput)
    def add_technology(
        name: str,
        version: str = None,
        type: str = "other",
        confidence: float = 0.5,
    ) -> str:
        """
        Record a detected technology.

        Call this when you identify a framework, language, server, etc.
        Types: framework, language, database, server, cms, library, auth, other
        """
        return f"Technology recorded: {name}"

    @tool(args_schema=AddEntryPointInput)
    def add_entry_point(
        location: str,
        type: str,
        input_type: str = "",
        validation_observed: str = "",
        notes: str = "",
    ) -> str:
        """
        Record a potential entry point for attacks.

        Call this when you find forms, parameters, file uploads, etc.
        Types: form, api, header, cookie, file_upload, query_param, path_param
        """
        return f"Entry point recorded: [{type}] {location}"

    @tool(args_schema=SetAuthInfoInput)
    def set_auth_info(
        auth_type: str,
        login_endpoint: str = None,
        registration_available: bool = False,
    ) -> str:
        """
        Record authentication information.

        Auth types: jwt, session, basic, oauth, api_key, none
        """
        return f"Auth info recorded: {auth_type}"

    @tool(args_schema=AddNoteInput)
    def add_note(note: str) -> str:
        """
        Add an observation or note.

        Use for anything interesting that doesn't fit other categories.
        """
        return "Note recorded."

    @tool(args_schema=ReconCompleteInput)
    def recon_complete(summary: str, priority_targets: list = None) -> str:
        """
        Mark reconnaissance as complete.

        Call this when you've finished gathering information.
        Include a summary and list priority targets for testing.
        """
        return "Recon complete. Returning to orchestrator."

    # Get task tools for progress tracking
    task_tools = get_task_tools()

    return [
        terminal,
        browser,
        add_endpoint,
        add_technology,
        add_entry_point,
        set_auth_info,
        add_note,
        recon_complete,
    ] + task_tools
