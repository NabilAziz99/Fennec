"""
Fennec AI Core Source Code.

This package contains the core AI agent code including:
- agents: Individual agent implementations (orchestrator, pentester, researcher, coder)
- graph: LangGraph workflow definitions
- state: State management for the agent graph
- orchestration: Hypothesis management and DFS-based exploration
- tools: Tools available to each agent
- prompts: System prompts and templates
- skills: Dynamic knowledge injection from markdown files
- schemas: Data schemas for inputs/outputs
- config: Configuration management
- docker: Docker container management
- api: FastAPI server
"""

from .state import (
    FennecState,
    AgentType,
    SessionContext,
    ContainerInfo,
    create_initial_state,
    # Hypothesis management
    Hypothesis,
    HypothesisTree,
    HypothesisStatus,
    HypothesisResult,
    Severity,
    AgentRole,
    AgentResult,
    NewHypothesisData,
)

from .orchestration import (
    HypothesisManager,
    create_manager,
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
    "AgentResult",
    "NewHypothesisData",
    # Orchestration
    "HypothesisManager",
    "create_manager",
]
