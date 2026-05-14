"""
Tools available to the coder agent.
"""

from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

try:
    from ..schemas import DelegateInput
    from .execution import create_browser_tool
except ImportError:
    from src.schemas import DelegateInput
    from src.tools.execution import create_browser_tool


def get_coder_tools(config: RunnableConfig):
    """Get tools for the coder agent."""

    browser = create_browser_tool()

    @tool(args_schema=DelegateInput)
    def delegate_researcher(task: str, context: str = "") -> str:
        """
        Delegate a research task to the researcher.

        Use for API documentation, library examples, or technical specs.
        """
        return f"Delegating to researcher: {task}"

    return [browser, delegate_researcher]
