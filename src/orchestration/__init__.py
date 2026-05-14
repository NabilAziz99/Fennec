"""
Orchestration module for Fennec AI.

Contains the HypothesisManager which implements DFS-based exploration
with blocking/unblocking logic for hypothesis management.
"""

from .hypothesis_manager import (
    HypothesisManager,
    create_manager,
)

__all__ = [
    "HypothesisManager",
    "create_manager",
]
