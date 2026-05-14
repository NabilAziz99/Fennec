"""
Tools module for Fennec AI agents.

Agent-callable tools:
- task_create, task_update, task_get, task_list: Internal step tracking
- report_result: Complete hypothesis + propose new ones

Role-based tools (4-role architecture):
- Recon tools: endpoint discovery, tech detection
- Pentester tools: security testing
- Coder tools: exploit development
- Orchestrator tools: routing & delegation
"""

from .orchestrator_tools import get_orchestrator_tools
from .pentester_tools import get_pentester_tools
from .coder_tools import get_coder_tools
from .hypothesis_tools import get_hypothesis_tools, report_result
from .task_tools import (
    get_task_tools,
    task_create,
    task_update,
    task_get,
    task_list,
)
from .recon_tools import get_recon_tools

__all__ = [
    "get_orchestrator_tools",
    "get_pentester_tools",
    "get_coder_tools",
    # Hypothesis reporting
    "get_hypothesis_tools",
    "report_result",
    # Task tools
    "get_task_tools",
    "task_create",
    "task_update",
    "task_get",
    "task_list",
    # Recon
    "get_recon_tools",
]
