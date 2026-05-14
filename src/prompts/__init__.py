"""
System prompts for Fennec AI agents.

Uses the modular prompt builder for hypothesis-driven testing.
"""

# Modular prompt builder
from .builder import (
    PromptBuilder,
    build_prompt,
)

# Prompt sections (for custom composition)
from .sections import (
    AUTHORIZATION,
    PERSISTENCE,
    METHODOLOGY,
    VULNERABILITY_FOCUS,
    ENVIRONMENT,
    get_agent_identity,
    get_testing_mode_prompt,
)

__all__ = [
    # Builder
    "PromptBuilder",
    "build_prompt",
    # Sections
    "AUTHORIZATION",
    "PERSISTENCE",
    "METHODOLOGY",
    "VULNERABILITY_FOCUS",
    "ENVIRONMENT",
    "get_agent_identity",
    "get_testing_mode_prompt",
]
