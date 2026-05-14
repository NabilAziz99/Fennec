"""
Hypothesis-based tools for agents.

These tools enable agents to report their findings in a structured way
that the hypothesis manager can process for routing and state updates.
"""

from langchain_core.tools import tool

try:
    from ..schemas import ReportResultInput, NewHypothesisInput
except ImportError:
    from src.schemas import ReportResultInput, NewHypothesisInput


@tool(args_schema=ReportResultInput)
def report_result(
    status: str,
    result: str = None,
    severity: str = None,
    outputs: list = None,
    findings: list = None,
    internal_steps: list = None,
    new_hypotheses: list = None,
    needs: list = None,
    error: str = None,
) -> str:
    """
    Report the results of your hypothesis exploration.

    CALL THIS WHEN YOU ARE DONE exploring the current hypothesis.

    Args:
        status: 'completed' | 'needs_info' | 'dead_end'
        result: (if completed) 'vulnerable' | 'safe' | 'inconclusive'
        severity: (if vulnerable) 'critical' | 'high' | 'medium' | 'low' | 'info'
        outputs: Things you produced (e.g., ['admin_credentials', 'session_token'])
        findings: What you discovered (e.g., ['SQLi confirmed on /login'])
        internal_steps: What you tried internally (for logging)
        new_hypotheses: New attack paths that need DIFFERENT agents
        needs: (if needs_info) What you're missing (e.g., ['payment_token'])
        error: (if dead_end) Why you can't proceed

    Returns:
        Confirmation message
    """
    # This is a "barrier" tool - the actual processing happens in the node
    # The tool just returns a confirmation message
    if status == "completed":
        if result == "vulnerable":
            return f"Reported: VULNERABLE ({severity}). Findings: {findings}"
        else:
            return f"Reported: {result}. Findings: {findings}"
    elif status == "needs_info":
        return f"Reported: NEEDS INFO. Missing: {needs}"
    else:
        return f"Reported: DEAD END. Reason: {error}"


def get_hypothesis_tools():
    """Get the hypothesis-related tools that all agents can use."""
    return [report_result]
