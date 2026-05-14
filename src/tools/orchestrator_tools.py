"""
Tools available to the orchestrator agent.
"""

from langchain_core.tools import tool

try:
    from ..schemas import (
        DelegateInput,
        SubtaskListInput,
        SubtaskUpdateInput,
        AskUserInput,
    )
except ImportError:
    from src.schemas import (
        DelegateInput,
        SubtaskListInput,
        SubtaskUpdateInput,
        AskUserInput,
    )


def get_orchestrator_tools():
    """Get tools for the orchestrator agent."""

    @tool(args_schema=DelegateInput)
    def pentester(task: str, context: str = "") -> str:
        """
        Delegate a security testing task to the pentester specialist.

        The pentester handles:
        - Network reconnaissance (nmap, masscan)
        - Web application testing (gobuster, sqlmap, nikto)
        - Vulnerability exploitation
        - Post-exploitation activities
        """
        return f"Delegating to pentester: {task}"

    @tool(args_schema=DelegateInput)
    def coder(task: str, context: str = "") -> str:
        """
        Delegate a coding task to the coder specialist.

        The coder handles:
        - Custom exploit development
        - Security tool creation
        - Automation scripts
        - Payload generation
        """
        return f"Delegating to coder: {task}"

    @tool(args_schema=DelegateInput)
    def researcher(task: str, context: str = "") -> str:
        """
        Delegate a research task to the researcher specialist.

        The researcher handles:
        - OSINT and reconnaissance
        - CVE and vulnerability research
        - Technical documentation lookup
        """
        return f"Delegating to researcher: {task}"

    @tool(args_schema=SubtaskListInput)
    def subtask_list(subtasks: list) -> str:
        """
        Create a plan by defining subtasks for the penetration test.

        Call this at the start to break down the task into steps.
        Each subtask should specify: title, description, assigned_agent
        """
        return f"Created {len(subtasks)} subtasks"

    @tool(args_schema=SubtaskUpdateInput)
    def subtask_update(subtask_index: int, status: str, result: str = "") -> str:
        """Update the status of a subtask."""
        return f"Updated subtask {subtask_index} to {status}"

    @tool(args_schema=AskUserInput)
    def ask_user(question: str, options: list = None) -> str:
        """
        Ask the user for clarification or input.

        Use when requirements are unclear or confirmation is needed.
        """
        return f"Asking user: {question}"

    return [pentester, coder, researcher, subtask_list, subtask_update, ask_user]
