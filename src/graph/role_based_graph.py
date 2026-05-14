"""
LangGraph builder for the simplified 4-role architecture.

Roles:
1. RECON - Maps attack surface
2. ANALYST - Forms hypotheses (runs ONCE after recon)
3. PENTESTER - Tests hypotheses (one at a time)
4. ORCHESTRATOR - Processes results + routes between roles (pure logic, not LLM)

Flow:
- START → RECON → ANALYST → ORCHESTRATOR (initial)
- ORCHESTRATOR → PENTESTER → ORCHESTRATOR (testing loop — no analyst in between)
- ORCHESTRATOR → RECON → ANALYST → ORCHESTRATOR (more recon loop)
- ORCHESTRATOR → END (done)

Fixed edges: RECON→ANALYST, PENTESTER→ORCHESTRATOR, ANALYST→ORCHESTRATOR
Conditional: ORCHESTRATOR decides next step
"""

from typing import Literal

from langgraph.graph import StateGraph, START, END

try:
    from ..state import FennecState, AgentType
    from ..agents import recon_node, emission_node, human_review_node
    from ..agents.analyst import analyst_node
    from ..agents.pentester import pentester_node
    from ..cli import (
        print_agent_header, print_status, print_hypothesis_tree,
        print_divider, print_header,
    )
except ImportError:
    from src.state import FennecState, AgentType
    from src.agents import recon_node, emission_node, human_review_node
    from src.agents.analyst import analyst_node
    from src.agents.pentester import pentester_node
    from src.cli import (
        print_agent_header, print_status, print_hypothesis_tree,
        print_divider, print_header,
    )


async def orchestrator_node(state: FennecState, config) -> dict:
    """
    Orchestrator node - pure routing logic + result processing.

    Responsibilities:
    1. Process pending pentester results (pure Python, no LLM)
    2. Route to next step:
       a. Have pending hypotheses? → PENTESTER
       b. Need more recon? → RECON
       c. Done? → END

    This is NOT an LLM agent - just routing logic and bookkeeping.
    """
    from ..orchestration import HypothesisManager
    from ..state import ReconData, CorrelationStore
    from ..state.hypothesis import AgentRole
    from ..agents.analyst import _process_pending_result

    print_agent_header("orchestrator")

    updates = {}

    # === Process pending pentester result (moved from analyst) ===
    manager = None
    if state.get("hypothesis_manager"):
        manager = HypothesisManager.from_dict(state["hypothesis_manager"])

    correlation_store = None
    if state.get("correlation_store"):
        correlation_store = CorrelationStore.from_dict(state["correlation_store"])
    else:
        correlation_store = CorrelationStore()

    pending_result = state.get("pending_agent_result")
    if pending_result and manager:
        _process_pending_result(
            pending_result=pending_result,
            current_hypothesis_id=state.get("current_hypothesis_id"),
            manager=manager,
            correlation_store=correlation_store,
        )
        updates["pending_agent_result"] = None
        updates["current_hypothesis_id"] = None
        updates["correlation_store"] = correlation_store.to_dict()
        updates["hypothesis_manager"] = manager.to_dict()

    # === Gather current state ===
    has_hypotheses = manager is not None
    pending_hypotheses = []
    if has_hypotheses:
        pending_hypotheses = [h for h in manager.tree.hypotheses.values()
                            if h.status is None or h.status.value == "pending"]

    finding_count = len(correlation_store.findings) if correlation_store else 0

    # === Decision logic ===

    # 1. Have pending hypotheses? Test them
    if pending_hypotheses:
        next_hyp = manager.get_next_hypothesis()

        if next_hyp:
            hypotheses_list = [
                {
                    "id": h.id,
                    "title": h.title,
                    "status": h.status.value if h.status else "pending",
                    "required_agent": h.required_agent.value if h.required_agent else "pentester",
                    "priority": h.priority,
                }
                for h in manager.tree.hypotheses.values()
            ]
            print_hypothesis_tree(hypotheses_list, current_id=next_hyp.id)
            print_status(f"Testing: {next_hyp.title[:50]}", status="info")

            updates["next_agent"] = AgentType.PENTESTER
            updates["current_hypothesis_id"] = next_hyp.id
            updates["hypothesis_manager"] = manager.to_dict()
            return updates

    # Check if analyst requested more recon
    agent_request = state.get("agent_request")
    forced_end_prefix: str | None = None
    if agent_request and agent_request.get("to") == "recon":
        # Hard cap on recon rounds to prevent analyst↔recon ping-pong.
        # The contract is: "dispense hypotheses one-by-one; when queue is empty, finish."
        # If analyst can't form a single hypothesis after MAX_RECON_ROUNDS passes,
        # the target is genuinely uncharacterizable — stop instead of looping forever.
        MAX_RECON_ROUNDS = 3
        rounds = int(state.get("recon_round_count", 0) or 0)
        if rounds >= MAX_RECON_ROUNDS:
            print_status(
                f"Recon round cap reached ({rounds}/{MAX_RECON_ROUNDS}) — ending run "
                "(analyst could not form hypotheses with available data)",
                status="warning",
            )
            forced_end_prefix = (
                f"⚠️  Analyst could not form testable hypotheses after {rounds} recon "
                f"round(s). Ending to avoid infinite analyst↔recon loop.\n"
                "Check recon_data — the target may be minimal or the recon tools "
                "may not have produced usable findings.\n\n"
            )
            updates["agent_request"] = None
            # Fall through to the END block below — it persists to the API.
        else:
            print_status(
                f"Analyst requested more recon (round {rounds + 1}/{MAX_RECON_ROUNDS}): "
                f"{agent_request.get('task', '')[:50]}",
                status="info",
            )
            updates["next_agent"] = AgentType.RECON
            updates["recon_round_count"] = rounds + 1
            return updates

    # 2. No more hypotheses (or recon cap hit) — we're done
    print_divider()
    print_header("PENETRATION TEST COMPLETE", char="═")
    updates["should_continue"] = False

    final_result = forced_end_prefix or ""
    final_result += "## Penetration Test Complete\n\n"

    if finding_count > 0:
        final_result += correlation_store.get_summary()

    if has_hypotheses:
        stats = manager.get_statistics()
        final_result += f"\n\n### Statistics\n"
        final_result += f"- Hypotheses tested: {stats['total']}\n"
        final_result += f"- Vulnerabilities found: {stats['vulnerabilities']}\n"

    updates["final_result"] = final_result
    updates["success"] = finding_count > 0

    return updates


def route_from_orchestrator(state: FennecState) -> Literal["pentester", "recon", "__end__"]:
    """
    Route from orchestrator.

    Orchestrator can only go to:
    - pentester (test hypothesis)
    - recon (more reconnaissance)
    - end (done)
    """
    if not state.get("should_continue", True):
        return "__end__"

    next_agent = state.get("next_agent")

    if next_agent == AgentType.PENTESTER:
        return "pentester"
    elif next_agent == AgentType.RECON:
        return "recon"
    else:
        return "__end__"


def route_from_recon(state: FennecState) -> Literal["recon", "analyst"]:
    """
    Route from recon.

    Recon can either:
    - Loop back to itself (more recon work needed)
    - Go to analyst (recon complete)
    """
    # Check if recon is complete
    recon_data = state.get("recon_data")
    if recon_data:
        from ..state import ReconData
        data = ReconData.from_dict(recon_data)
        if data.recon_completed is not None:
            return "analyst"

    # Not complete yet, loop back
    return "recon"


def create_role_based_graph(htli: bool = False) -> StateGraph:
    """
    Create the simplified 4-role state graph.

    Nodes:
    - recon: Maps attack surface (can loop until complete)
    - analyst: Forms hypotheses (runs once after recon)
    - pentester: Tests hypotheses (one at a time)
    - orchestrator: Processes results + routes (pure logic, no LLM)
    - human_review: (optional, HTLI mode) operator approval gate before pentester

    Flow (HTLI disabled):
    - START → recon → analyst → orchestrator → pentester | recon | END
    - pentester → orchestrator (orchestrator processes result + picks next)

    Flow (HTLI enabled):
    - analyst → human_review → orchestrator  (instead of direct)
    """
    graph = StateGraph(FennecState)

    # Add nodes
    graph.add_node("recon", recon_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("pentester", pentester_node)
    graph.add_node("orchestrator", orchestrator_node)

    if htli:
        graph.add_node("human_review", human_review_node)

    # Entry point
    graph.add_edge(START, "recon")

    # Recon can loop or go to analyst
    graph.add_conditional_edges(
        "recon",
        route_from_recon,
        {
            "recon": "recon",
            "analyst": "analyst",
        }
    )

    # Fixed edges
    graph.add_edge("pentester", "orchestrator")  # After testing, orchestrator processes result + picks next

    if htli:
        # analyst → human_review → orchestrator
        graph.add_edge("analyst", "human_review")
        graph.add_edge("human_review", "orchestrator")
    else:
        graph.add_edge("analyst", "orchestrator") # Analyst returns to orchestrator

    graph.add_conditional_edges(
        "orchestrator",
        route_from_orchestrator,
        {
            "pentester": "pentester",
            "recon": "recon",
            "__end__": END,
        }
    )

    return graph

def create_test_recon_graph():
    """Create the recon graph."""
    graph = StateGraph(FennecState)
    graph.add_node("recon", recon_node)
    graph.add_node("emission", emission_node)
    graph.add_edge(START, "recon")
    graph.add_edge("recon", "emission")
    graph.add_edge("emission", END)
    return graph

def compile_role_based_graph(graph_name="main", htli: bool = False):
    """Create and compile the 4-role graph."""
    if graph_name == "main":
        graph_builder = create_role_based_graph(htli=htli)
        if htli:
            from langgraph.checkpoint.memory import MemorySaver
            return graph_builder.compile(checkpointer=MemorySaver())
        return graph_builder.compile()
    elif graph_name == "recon":
        return create_test_recon_graph().compile()
