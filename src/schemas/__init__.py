"""
Pydantic schemas for Fennec AI tools and structured outputs.
"""

from .tool_inputs import (
    TerminalInput,
    FileReadInput,
    FileWriteInput,
    BrowserInput,
    WebSearchInput,
)

from .recon_result import (
    EndpointResult,
    TechnologyResult,
    EntryPointResult,
    ReconResult,
)
from .analyst_result import HypothesisData, AnalystResult
from .pentester_result import PentesterResult
from .coder_result import CoderResult

from .delegation import (
    DelegateInput,
    SubtaskItem,
    SubtaskListInput,
    SubtaskUpdateInput,
    AskUserInput,
)

from .hypothesis_tools import (
    ReportResultInput,
    NewHypothesisInput,
)

__all__ = [
    # Tool inputs
    "TerminalInput",
    "FileReadInput",
    "FileWriteInput",
    "BrowserInput",
    "WebSearchInput",
    # Recon result
    "EndpointResult",
    "TechnologyResult",
    "EntryPointResult",
    "ReconResult",
    # Analyst result
    "HypothesisData",
    "AnalystResult",
    # Pentester result
    "PentesterResult",
    # Coder result
    "CoderResult",
    # Delegation
    "DelegateInput",
    "SubtaskItem",
    "SubtaskListInput",
    "SubtaskUpdateInput",
    "AskUserInput",
    # Hypothesis tools
    "ReportResultInput",
    "NewHypothesisInput",
]
