"""
LangGraph state schema for Fennec AI.

Uses TypedDict with Annotated for proper reducer support.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Annotated, Optional
from typing_extensions import TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentType(str, Enum):
    """Graph-level node identifiers for LangGraph routing.

    These correspond to actual graph nodes in ``src/graph/builder.py``.
    Compare with :class:`~src.state.hypothesis.AgentRole` which
    identifies the *role* that a hypothesis is assigned to (and includes
    ``CODER``, which is a sub-agent, not a graph node).
    """
    ORCHESTRATOR = "orchestrator"  # Routes between agents (pure logic)
    RECON = "recon"                # Maps attack surface
    ANALYST = "analyst"            # Forms hypotheses + analyzes results
    PENTESTER = "pentester"        # Tests hypotheses (unified tester)


@dataclass
class ContainerInfo:
    """Docker container information."""
    container_id: str
    image: str
    working_dir: str = "/work"


@dataclass
class SessionContext:
    """Session context for a penetration testing run."""
    session_id: str
    flow_id: str
    container: Optional[ContainerInfo] = None
    docker_image: str = "fennec-linux" # kalilinux/kali-rolling:latest
    language: str = "en"
    created_at: datetime = field(default_factory=datetime.utcnow)


class BlockedHypothesisDict(TypedDict):
    """Serialized form of a single blocked-hypothesis entry."""
    hypothesis_id: str
    waiting_for: str
    blocked_at: str  # ISO-8601


class HypothesisManagerDict(TypedDict, total=False):
    """Serialized form produced by ``HypothesisManager.to_dict()``.

    Kept here (rather than in ``orchestration/``) so that FennecState can
    reference a concrete shape instead of an opaque ``dict``.

    Fields
    ------
    tree : dict[str, dict]
        Hypothesis ID -> serialized Hypothesis.
    pending_queue : list[str]
        Hypothesis IDs ordered by priority (highest at end, dequeued first).
    blocked_list : list[BlockedHypothesisDict]
        Hypotheses waiting on outputs from other hypotheses.
    outputs_registry : dict[str, str]
        output_name -> hypothesis ID that produced it.
    pending_outputs : dict[str, str]
        output_name -> hypothesis ID that claims it will produce it.
    current_hypothesis_id : str | None
        The hypothesis currently being explored.
    """
    tree: dict[str, dict]
    pending_queue: list[str]
    blocked_list: list[BlockedHypothesisDict]
    outputs_registry: dict[str, str]
    pending_outputs: dict[str, str]
    current_hypothesis_id: Optional[str]


class FennecState(TypedDict):
    """
    Main state for Fennec AI LangGraph.

    Uses add_messages reducer for message history management.
    Other fields use default overwrite behavior.
    """

    # ── Session & messages ──────────────────────────────────────
    session: SessionContext
    messages: Annotated[list[AnyMessage], add_messages]

    # ── Target ──────────────────────────────────────────────────
    target_url: Optional[str]
    task_description: Optional[str]
    task_hint: Optional[str]

    # ── Routing & flow control ──────────────────────────────────
    next_agent: Optional[AgentType]
    should_continue: bool

    # ── Final output ────────────────────────────────────────────
    final_result: Optional[str]
    success: bool

    # ── Hypothesis-based exploration ────────────────────────────
    hypothesis_manager: Optional[HypothesisManagerDict]
    current_hypothesis_id: Optional[str]
    pending_agent_result: Optional[dict]  # Latest agent result for orchestrator
    has_source_code: bool
    has_live_target: bool

    # ── Recon & correlation ─────────────────────────────────────
    recon_data: Optional[dict]            # Serialized ReconData
    correlation_store: Optional[dict]     # Serialized CorrelationStore
    agent_request: Optional[dict]         # Inter-agent request
    recon_round_count: int                # Number of recon invocations so far (cap to prevent analyst↔recon loops)

    # ── Authentication credentials ─────────────────────────────
    auth_credentials: Optional[dict]  # {"username": "...", "password": "...", "auth_type": "..."}

    # ── Assessment method ─────────────────────────────────────
    method: Optional[str]  # "turbo" | "balanced" | "deep"

def create_initial_state(
    session: SessionContext,
    target_url: str,
    has_source_code: bool = False,
    has_live_target: bool = True,
    task_description: Optional[str] = None,
    task_hint: Optional[str] = None,
    initial_hypotheses: list = None,
    initial_recon_data: Optional[dict] = None,
    auth_credentials: Optional[dict] = None,
    method: Optional[str] = None,
) -> FennecState:
    """
    Create initial state for a new penetration testing run.

    Args:
        session: Session context with container info
        target_url: Target URL to test
        has_source_code: Whether source code is available (white-box)
        has_live_target: Whether a live target is available
        initial_hypotheses: Optional list of initial hypotheses to seed

    Returns:
        Initialized FennecState
    """
    from langchain_core.messages import HumanMessage

    # Create hypothesis manager state
    hypothesis_manager_state = None
    if initial_hypotheses:
        from ..orchestration import create_manager
        manager = create_manager(initial_hypotheses)
        hypothesis_manager_state = manager.to_dict()

    return FennecState(
        session=session,
        messages=[HumanMessage(content=f"Perform penetration testing on: {target_url}")],
        target_url=target_url,
        task_description=task_description,
        task_hint=task_hint,
        next_agent=AgentType.ORCHESTRATOR,
        should_continue=True,
        final_result=None,
        success=False,
        hypothesis_manager=hypothesis_manager_state,
        current_hypothesis_id=None,
        pending_agent_result=None,
        has_source_code=has_source_code,
        has_live_target=has_live_target,
        recon_data=initial_recon_data,
        correlation_store=None,
        auth_credentials=auth_credentials,
        method=method,
        agent_request=None,
        recon_round_count=0,
    )
