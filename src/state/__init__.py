"""
LangGraph state definitions for Fennec AI.

This module contains the state schema used throughout the graph,
including hypothesis management for DFS-based exploration.
"""

from .graph_state import (
    FennecState,
    AgentType,
    SessionContext,
    ContainerInfo,
    create_initial_state,
)

from .hypothesis import (
    Hypothesis,
    HypothesisTree,
    HypothesisStatus,
    HypothesisResult,
    Severity,
    AgentRole,
)

from .task import (
    Task,
    TaskStore,
    Todo,      # Alias for backwards compatibility
    TodoList,  # Alias for backwards compatibility
)

from .agent_result import (
    AgentResult,
    NewHypothesisData,
)

from .recon import (
    ReconData,
    Technology,
    TechnologyType,
    Endpoint,
    EntryPoint,
)

from .correlation import (
    Finding,
    FindingSeverity,
    FindingStatus,
    Correlation,
    CorrelationStore,
)

__all__ = [
    # Core state
    "FennecState",
    "AgentType",
    "SessionContext",
    "ContainerInfo",
    "create_initial_state",
    # Hypothesis management
    "Hypothesis",
    "HypothesisTree",
    "HypothesisStatus",
    "HypothesisResult",
    "Severity",
    "AgentRole",
    # Task management (Claude Code style)
    "Task",
    "TaskStore",
    "Todo",      # Alias
    "TodoList",  # Alias
    # Agent results
    "AgentResult",
    "NewHypothesisData",
    # Recon data
    "ReconData",
    "Technology",
    "TechnologyType",
    "Endpoint",
    "EntryPoint",
    # Correlation
    "Finding",
    "FindingSeverity",
    "FindingStatus",
    "Correlation",
    "CorrelationStore",
]
