"""
LangGraph node functions for Fennec AI agents.

Simplified 4-role architecture:
1. RECON - Maps attack surface (create_agent + ToolStrategy)
2. ANALYST - Forms hypotheses + analyzes results (create_agent + ToolStrategy)
3. PENTESTER - Tests hypotheses (create_agent + ToolStrategy, can invoke CODER)
4. ORCHESTRATOR - Routes between agents (in role_based_graph.py)

All agents use create_agent with structured output via ToolStrategy.
"""

# Core agents for 4-role architecture
from .recon import recon_node
from .emission import emission_node
from .analyst import analyst_node
from .pentester import pentester_node
from .human_review import human_review_node

# Coder sub-agent (invoked by pentester, not a graph node)
from .coder import run_coder

__all__ = [
    # Graph nodes
    "recon_node",
    "emission_node",
    "analyst_node",
    "pentester_node",
    "human_review_node",
    # Sub-agent utilities
    "run_coder",
]
