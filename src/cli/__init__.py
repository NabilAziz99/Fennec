"""
CLI module for Fennec AI.

Provides visualization and logging utilities.

Output Configuration:
    from src.cli import VisualizerConfig

    # Disable CLI output (useful for tests or headless runs)
    VisualizerConfig.disable_cli()

    # Disable logging output (if you only want CLI output)
    VisualizerConfig.disable_logging()

    # Both are enabled by default
"""

from .visualizer import (
    print_header,
    print_agent_header,
    print_tool_call,
    print_tool_result,
    print_hypothesis_tree,
    print_hypothesis_added,
    print_hypothesis_completed,
    print_finding,
    print_correlation,
    print_recon_summary,
    print_progress,
    print_status,
    print_divider,
    Colors,
    VisualizerConfig,
)

__all__ = [
    "print_header",
    "print_agent_header",
    "print_tool_call",
    "print_tool_result",
    "print_hypothesis_tree",
    "print_hypothesis_added",
    "print_hypothesis_completed",
    "print_finding",
    "print_correlation",
    "print_recon_summary",
    "print_progress",
    "print_status",
    "print_divider",
    "Colors",
    "VisualizerConfig",
]
