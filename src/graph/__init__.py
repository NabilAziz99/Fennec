"""
LangGraph definition for Fennec AI.

Simplified 4-role architecture:
1. RECON - Maps attack surface (can loop until complete)
2. ANALYST - Forms hypotheses + analyzes results
3. PENTESTER - Tests hypotheses (unified tester)
4. ORCHESTRATOR - Routes between agents (pure logic)

Flow:
- START → recon → analyst → orchestrator
- orchestrator → pentester → analyst → orchestrator (testing loop)
- orchestrator → recon → analyst → orchestrator (more recon loop)
- orchestrator → END (done)
"""

from .role_based_graph import create_role_based_graph, compile_role_based_graph

__all__ = [
    "create_role_based_graph",
    "compile_role_based_graph",
]
