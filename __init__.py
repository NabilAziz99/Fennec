"""
Fennec - Open-source, AI-driven penetration testing framework.

A multi-agent system with 4 role-based agents:
- Recon: Attack surface mapping
- Analyst: Hypothesis formation and analysis
- Pentester: Security testing and exploitation
- Coder: Code generation and exploit development
"""


def __getattr__(name: str):
    if name == "FennecConfig" or name == "get_config":
        from .src.config import FennecConfig, get_config
        return FennecConfig if name == "FennecConfig" else get_config
    if name == "compile_role_based_graph":
        from .src.graph import compile_role_based_graph
        return compile_role_based_graph
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__version__ = "0.1.0"
__all__ = ["FennecConfig", "get_config", "compile_role_based_graph"]
