"""
Human Review Node — Human-In-The-Loop (HTLI) support.

Inserted between the analyst and the orchestrator.  Uses LangGraph
`interrupt()` to fully suspend the graph until the operator reviews
hypotheses via the web UI or CLI.

The interrupt payload contains the current hypotheses snapshot.
The resume value is a user_edits dict with approved/rejected edits,
new hypotheses, and optional guidance notes.
"""

from __future__ import annotations

import logging

from langgraph.types import interrupt

logger = logging.getLogger("fennec.human_review")

try:
    from ..orchestration import HypothesisManager
    from ..state.hypothesis import (
        Hypothesis,
        HypothesisStatus,
        AgentRole,
    )
except ImportError:
    from src.orchestration import HypothesisManager
    from src.state.hypothesis import (
        Hypothesis,
        HypothesisStatus,
        AgentRole,
    )


def _build_interrupt_payload(state: dict) -> dict:
    """Build the payload sent to the operator for review."""
    hypothesis_manager_dict = state.get("hypothesis_manager")
    hypotheses_snapshot = []

    if hypothesis_manager_dict:
        try:
            manager = HypothesisManager.from_dict(hypothesis_manager_dict)
            for h in manager.tree.hypotheses.values():
                hypotheses_snapshot.append(h.to_dict())
        except Exception as exc:
            logger.warning(f"Failed to build hypotheses snapshot: {exc}")

    return {
        "type": "hypothesis_review",
        "hypotheses": hypotheses_snapshot,
    }


def _apply_edits(hypothesis_manager_dict: dict, user_edits: dict) -> dict:
    """Apply user edits to the hypothesis manager and return state updates."""
    manager = HypothesisManager.from_dict(hypothesis_manager_dict)

    logger.info(f"Applying edits: {len(user_edits.get('edits', []))} edits, "
                f"{len(user_edits.get('new_hypotheses', []))} new hypotheses")
    logger.debug(f"user_edits payload: {user_edits}")

    for edit in user_edits.get("edits", []):
        hyp_id = edit["hypothesis_id"]
        hyp = manager.tree.hypotheses.get(hyp_id)
        if not hyp:
            logger.warning(f"Hypothesis {hyp_id} not found in manager. "
                           f"Available IDs: {list(manager.tree.hypotheses.keys())}")
            continue

        if edit["action"] == "reject":
            logger.info(f"Rejecting hypothesis '{hyp.title}' ({hyp_id})")
            hyp.status = HypothesisStatus.DEAD_END
            if hyp.id in manager.pending_queue:
                manager.pending_queue.remove(hyp.id)
        else:  # approve
            changes = []
            if edit.get("title"):
                hyp.title = edit["title"]
                changes.append(f"title='{edit['title']}'")
            if edit.get("description"):
                hyp.description = edit["description"]
                changes.append("description updated")
            if edit.get("priority") is not None:
                hyp.priority = edit["priority"]
                changes.append(f"priority={edit['priority']}")
                # Re-sort queue by removing and re-inserting
                if hyp.id in manager.pending_queue:
                    manager.pending_queue.remove(hyp.id)
                    manager._enqueue(hyp.id)
            logger.info(f"Approved hypothesis '{hyp.title}' ({hyp_id})"
                        f"{' with changes: ' + ', '.join(changes) if changes else ''}")

    for new in user_edits.get("new_hypotheses", []):
        logger.info(f"Adding new hypothesis: '{new['title']}'")
        manager.add_hypothesis(Hypothesis(
            title=new["title"],
            description=new.get("description", ""),
            priority=new.get("priority", 0.5),
            skills=new.get("skills", []),
            required_agent=AgentRole(new.get("required_agent", "pentester")),
        ))

    logger.info(f"After edits: {len(manager.pending_queue)} hypotheses in pending queue")

    updates: dict = {"hypothesis_manager": manager.to_dict()}

    if user_edits.get("guidance_notes"):
        from langchain_core.messages import HumanMessage
        updates["messages"] = [
            HumanMessage(content=f"[OPERATOR GUIDANCE]: {user_edits['guidance_notes']}")
        ]

    return updates


async def human_review_node(state: dict, config) -> dict:
    """
    Pause for human review after the analyst runs.

    Uses LangGraph interrupt() to suspend the graph. The resume value
    is a user_edits dict containing approved/rejected edits, new
    hypotheses, and optional guidance notes.
    """
    payload = _build_interrupt_payload(state)

    logger.info(
        f"Interrupting for human review: {len(payload['hypotheses'])} hypotheses"
    )

    # Suspend the graph — returns user_edits when resumed
    user_edits = interrupt(payload)

    # Log what we received
    logger.info(f"Resumed with user_edits keys: {list(user_edits.keys()) if isinstance(user_edits, dict) else type(user_edits)}")
    logger.info(f"user_edits: {user_edits}")

    # Handle abort
    if user_edits is None or user_edits.get("abort"):
        logger.info("Operator aborted the run")
        return {"should_continue": False}

    # Apply edits if we have a hypothesis manager
    hypothesis_manager_dict = state.get("hypothesis_manager")
    has_edits = bool(user_edits.get("edits"))
    has_new = bool(user_edits.get("new_hypotheses"))
    logger.info(f"has hypothesis_manager: {bool(hypothesis_manager_dict)}, "
                f"has edits: {has_edits} ({len(user_edits.get('edits', []))}), "
                f"has new: {has_new} ({len(user_edits.get('new_hypotheses', []))})")

    if hypothesis_manager_dict and (has_edits or has_new):
        updates = _apply_edits(hypothesis_manager_dict, user_edits)
        logger.info("Applied operator edits to hypothesis manager")
        return updates

    # Guidance notes only (no hypothesis edits)
    if user_edits.get("guidance_notes"):
        from langchain_core.messages import HumanMessage
        return {
            "messages": [
                HumanMessage(
                    content=f"[OPERATOR GUIDANCE]: {user_edits['guidance_notes']}"
                )
            ]
        }

    # Simple approval — no changes
    logger.info("Operator approved without changes")
    return {}
