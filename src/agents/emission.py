"""
Emission node - renders recon-related state for terminal output.
"""

import json
from typing import Any

from langchain_core.runnables import RunnableConfig

try:
    from ..state import FennecState
    from ..cli import print_header, print_status, print_divider, VisualizerConfig
    from ..cli.visualizer import viz_logger
except ImportError:
    from src.state import FennecState
    from src.cli import print_header, print_status, print_divider, VisualizerConfig
    from src.cli.visualizer import viz_logger


def _emit_block(title: str, payload: Any) -> None:
    print_status(title, status="info")
    text = json.dumps(payload, indent=2, sort_keys=True, default=str)

    if VisualizerConfig.cli_enabled:
        print(text)

    if VisualizerConfig.log_enabled:
        for line in text.splitlines():
            print(line)


async def emission_node(state: FennecState, config: RunnableConfig) -> dict[str, Any]:
    """Emit recon-related state to terminal/logs."""
    print_header("RECON EMISSION", char="═")

    payload = {
        "target_url": state.get("target_url"),
        "recon_data": state.get("recon_data"),
        "correlation_store": state.get("correlation_store"),
        "agent_request": state.get("agent_request"),
    }

    _emit_block("Recon data + related fields", payload)
    print_divider()

    return {"next_agent": "END", "data":payload}
