"""
Modular prompt sections.

These sections are extracted from Strix's high-quality prompts and organized
for dynamic composition based on context.
"""

from .authorization import AUTHORIZATION
from .persistence import PERSISTENCE
from .testing_modes import BLACK_BOX_MODE, WHITE_BOX_MODE, COMBINED_MODE, get_testing_mode_prompt
from .methodology import METHODOLOGY
from .vulnerability_focus import VULNERABILITY_FOCUS
from .environment import ENVIRONMENT
from .todo_list import TODO_LIST
from .agent_identities import (
    RECON_IDENTITY,
    ANALYST_IDENTITY,
    PENTESTER_IDENTITY,
    CODER_IDENTITY,
    get_agent_identity,
)
from .agent_rules import get_agent_rules
__all__ = [
    "AUTHORIZATION",
    "PERSISTENCE",
    "BLACK_BOX_MODE",
    "WHITE_BOX_MODE",
    "COMBINED_MODE",
    "get_testing_mode_prompt",
    "METHODOLOGY",
    "VULNERABILITY_FOCUS",
    "ENVIRONMENT",
    "RECON_IDENTITY",
    "ANALYST_IDENTITY",
    "PENTESTER_IDENTITY",
    "CODER_IDENTITY",
    "TODO_LIST",
    "get_agent_identity",
    "get_agent_rules",
]
