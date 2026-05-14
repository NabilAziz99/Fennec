"""
Hypothesis Manager for priority-based penetration testing exploration.

The HypothesisManager is the core orchestration component that:
1. Maintains a priority queue of hypotheses to explore (highest priority first)
2. Tracks blocked hypotheses waiting for outputs
3. Manages a global outputs registry for dependency resolution
4. Processes agent results to update the hypothesis tree
5. Handles unblocking when outputs become available
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import logging

from ..state.hypothesis import (
    Hypothesis,
    HypothesisTree,
    HypothesisStatus,
    HypothesisResult,
    Severity,
    AgentRole,
)
from ..state.agent_result import AgentResult, NewHypothesisData

logger = logging.getLogger(__name__)


@dataclass
class BlockedHypothesis:
    """A hypothesis that's waiting for an output."""
    hypothesis_id: str
    waiting_for: str  # The output name it needs
    blocked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class HypothesisManager:
    """
    Manages hypothesis exploration using priority queue.

    Key concepts:
    - Priority Queue: Hypotheses to explore, ordered by priority (highest first)
    - Blocked List: Hypotheses waiting for outputs from other hypotheses
    - Outputs Registry: Global map of output_name -> hypothesis_id that produced it
    - Pending Outputs: Outputs that hypotheses claim they will produce

    Workflow:
    1. get_next_hypothesis() - Get highest priority hypothesis from queue
    2. Agent processes hypothesis and returns AgentResult
    3. handle_result() - Process the result, update tree, check unblocks
    4. Repeat until queue and blocked list are empty
    """

    # The hypothesis tree
    tree: HypothesisTree = field(default_factory=HypothesisTree)

    # Priority queue - list of hypothesis IDs, sorted by priority (highest at end)
    pending_queue: list[str] = field(default_factory=list)

    # Blocked hypotheses waiting for outputs
    blocked_list: list[BlockedHypothesis] = field(default_factory=list)

    # Map of output_name -> hypothesis_id that produced it
    outputs_registry: dict[str, str] = field(default_factory=dict)

    # Map of output_name -> hypothesis_id that claims it will produce it
    pending_outputs: dict[str, str] = field(default_factory=dict)

    # Currently active hypothesis
    current_hypothesis_id: Optional[str] = None

    def add_hypothesis(self, hypothesis: Hypothesis, parent_id: Optional[str] = None) -> str:
        """
        Add a new hypothesis to the tree and priority queue.

        Args:
            hypothesis: The hypothesis to add
            parent_id: Optional parent hypothesis ID

        Returns:
            The hypothesis ID
        """
        # Set parent if provided
        if parent_id:
            hypothesis.parent_id = parent_id

        # Add to tree
        self.tree.add(hypothesis)

        # Register expected outputs
        for output in hypothesis.expected_outputs:
            self.pending_outputs[output] = hypothesis.id

        # Add to priority queue (sorted by priority)
        self._enqueue(hypothesis.id)

        logger.info(f"Added hypothesis {hypothesis.id}: {hypothesis.title}")
        return hypothesis.id

    def get_next_hypothesis(self) -> Optional[Hypothesis]:
        """
        Get the next hypothesis to explore.

        Returns the highest priority hypothesis from the queue.

        Returns:
            The next hypothesis to explore, or None if done
        """
        # Check for unblocks first (outputs may have become available)
        self._check_all_unblocks()

        if not self.pending_queue:
            if self.blocked_list:
                logger.warning(f"Queue empty but {len(self.blocked_list)} hypotheses still blocked")
            return None

        # Pop highest priority hypothesis
        hypothesis_id = self.pending_queue.pop()
        hypothesis = self.tree.get(hypothesis_id)

        if not hypothesis:
            logger.error(f"Hypothesis {hypothesis_id} not found in tree")
            return self.get_next_hypothesis()  # Try next

        # Mark as in progress
        hypothesis.status = HypothesisStatus.IN_PROGRESS
        hypothesis.started_at = datetime.now(timezone.utc)
        self.current_hypothesis_id = hypothesis_id

        logger.info(f"Starting hypothesis {hypothesis.id}: {hypothesis.title}")
        return hypothesis

    def handle_result(self, result: AgentResult) -> Optional[str]:
        """
        Process an agent's result for the current hypothesis.

        Args:
            result: The AgentResult from the agent

        Returns:
            The next agent type to route to, or None if staying with current agent
        """
        if not self.current_hypothesis_id:
            logger.error("No current hypothesis to handle result for")
            return None

        hypothesis = self.tree.get(self.current_hypothesis_id)
        if not hypothesis:
            logger.error(f"Current hypothesis {self.current_hypothesis_id} not found")
            return None

        # Handle based on status
        if result.status == "completed":
            self._handle_completed(hypothesis, result)
        elif result.status == "needs_info":
            self._handle_needs_info(hypothesis, result)
        elif result.status == "dead_end":
            self._handle_dead_end(hypothesis, result)

        # Add new hypotheses as children
        for new_hyp_data in result.new_hypotheses:
            self._create_child_hypothesis(hypothesis.id, new_hyp_data)

        # Clear current hypothesis
        self.current_hypothesis_id = None

        # Determine routing
        # If there are more hypotheses, continue
        # Otherwise signal completion
        next_hyp = self._peek_next_hypothesis()
        if next_hyp:
            return next_hyp.required_agent.value

        return None  # Done

    def _handle_completed(self, hypothesis: Hypothesis, result: AgentResult) -> None:
        """Handle a completed hypothesis result."""
        hypothesis.status = HypothesisStatus.COMPLETED
        hypothesis.completed_at = datetime.now(timezone.utc)

        if result.result:
            hypothesis.result = HypothesisResult(result.result)

        if result.severity:
            hypothesis.severity = Severity(result.severity)

        # Auto-promote expected_outputs when vulnerable.
        # The analyst declared these upfront; the pentester confirmed the vuln,
        # so the artifacts (e.g. stolen creds) are now available.
        outputs = result.outputs or []
        if hypothesis.result == HypothesisResult.VULNERABLE:
            for expected in hypothesis.expected_outputs:
                if expected not in outputs:
                    outputs.append(expected)

        for output in outputs:
            self.outputs_registry[output] = hypothesis.id
            self.pending_outputs.pop(output, None)

        logger.info(
            f"Hypothesis {hypothesis.id} completed: {result.result}"
            f" (outputs: {outputs})"
        )

        # Check if any blocked hypotheses can now proceed
        self._check_all_unblocks()

    def _handle_needs_info(self, hypothesis: Hypothesis, result: AgentResult) -> None:
        """Handle a hypothesis that needs information from another hypothesis."""
        for need in result.needs:
            # Check if the need is already satisfied
            if need in self.outputs_registry:
                # Output already exists - this shouldn't block
                logger.info(f"Need '{need}' already available from {self.outputs_registry[need]}")
                continue

            # Check if any pending hypothesis will produce this
            if need in self.pending_outputs:
                # Block on that hypothesis
                provider_id = self.pending_outputs[need]
                hypothesis.status = HypothesisStatus.BLOCKED
                hypothesis.blocked_by = provider_id
                hypothesis.waiting_for = need

                self.blocked_list.append(BlockedHypothesis(
                    hypothesis_id=hypothesis.id,
                    waiting_for=need,
                ))

                logger.info(
                    f"Hypothesis {hypothesis.id} blocked waiting for "
                    f"'{need}' from {provider_id}"
                )
            else:
                # No one will produce this - create a new hypothesis to find it
                self._create_hypothesis_for_need(hypothesis.id, need)

    def _handle_dead_end(self, hypothesis: Hypothesis, result: AgentResult) -> None:
        """Handle a hypothesis that cannot proceed."""
        hypothesis.status = HypothesisStatus.DEAD_END
        hypothesis.completed_at = datetime.now(timezone.utc)

        logger.info(f"Hypothesis {hypothesis.id} is a dead end: {result.error}")

        # Remove from pending outputs
        for output in hypothesis.expected_outputs:
            self.pending_outputs.pop(output, None)

    def _create_child_hypothesis(
        self,
        parent_id: str,
        data: NewHypothesisData
    ) -> str:
        """Create a child hypothesis from agent-provided data."""
        hypothesis = Hypothesis(
            parent_id=parent_id,
            title=data.title,
            description=data.description,
            required_agent=AgentRole(data.required_agent),
            skills=data.skills,
            priority=data.priority,
            expected_outputs=data.expected_outputs,
        )

        return self.add_hypothesis(hypothesis, parent_id)

    def _create_hypothesis_for_need(self, requester_id: str, need: str) -> str:
        """
        Create a new hypothesis to satisfy a need.

        When an agent needs something that no existing hypothesis will produce,
        we create a new hypothesis to find it.
        """
        # Determine the appropriate agent based on the need type
        agent, skills = self._infer_agent_for_need(need)

        hypothesis = Hypothesis(
            title=f"Obtain {need}",
            description=f"Find or extract {need} required by hypothesis {requester_id}",
            required_agent=agent,
            skills=skills,
            priority=0.6,  # Slightly above default since it's a dependency
            expected_outputs=[need],
        )

        hyp_id = self.add_hypothesis(hypothesis)

        # Block the requester on this new hypothesis
        requester = self.tree.get(requester_id)
        if requester:
            requester.status = HypothesisStatus.BLOCKED
            requester.blocked_by = hyp_id
            requester.waiting_for = need

            self.blocked_list.append(BlockedHypothesis(
                hypothesis_id=requester_id,
                waiting_for=need,
            ))

        logger.info(
            f"Created hypothesis {hyp_id} to obtain '{need}' "
            f"for {requester_id}"
        )

        return hyp_id

    def _infer_agent_for_need(self, need: str) -> tuple[AgentRole, list[str]]:
        """
        Infer the appropriate agent and skills for a need.

        This is a heuristic based on common need patterns.
        """
        need_lower = need.lower()

        # Authentication/credential related
        if any(x in need_lower for x in ["credential", "password", "token", "session", "auth", "api_key"]):
            return AgentRole.PENTESTER, ["authentication", "credential_extraction"]

        # Database related
        if any(x in need_lower for x in ["database", "db_", "sql", "schema", "table"]):
            return AgentRole.PENTESTER, ["sql_injection", "database_exploitation"]

        # Code/source related
        if any(x in need_lower for x in ["source", "code", "config", "file"]):
            return AgentRole.CODER, ["code_analysis"]

        # Infrastructure related - pentester handles this
        if any(x in need_lower for x in ["server", "port", "service", "infra"]):
            return AgentRole.PENTESTER, ["reconnaissance"]

        # Research related — pentester handles this with web_search tool
        if any(x in need_lower for x in ["cve", "exploit", "vulnerability", "research"]):
            return AgentRole.PENTESTER, ["vulnerability_research"]

        # Default to pentester
        return AgentRole.PENTESTER, []

    def _check_all_unblocks(self) -> None:
        """Check if any blocked hypotheses can be unblocked."""
        unblocked = []

        for blocked in self.blocked_list:
            if blocked.waiting_for in self.outputs_registry:
                # Output is now available
                hypothesis = self.tree.get(blocked.hypothesis_id)
                if hypothesis:
                    hypothesis.status = HypothesisStatus.PENDING
                    hypothesis.blocked_by = None
                    hypothesis.waiting_for = None

                    # Re-add to queue
                    self._enqueue(blocked.hypothesis_id)

                    logger.info(
                        f"Unblocked hypothesis {blocked.hypothesis_id} - "
                        f"'{blocked.waiting_for}' is now available"
                    )

                unblocked.append(blocked)

        # Remove unblocked from blocked list
        for blocked in unblocked:
            self.blocked_list.remove(blocked)

    def _enqueue(self, hypothesis_id: str) -> None:
        """
        Add a hypothesis to the priority queue.

        Maintains priority order: higher priority at the end (dequeued first).
        Queue order: [low_priority, ..., high_priority]
        """
        hypothesis = self.tree.get(hypothesis_id)
        if not hypothesis:
            return

        # Find insertion point to maintain ascending priority order
        # We want: lowest priority at index 0, highest at end
        insert_idx = 0
        for i, other_id in enumerate(self.pending_queue):
            other = self.tree.get(other_id)
            if other and other.priority <= hypothesis.priority:
                insert_idx = i + 1

        self.pending_queue.insert(insert_idx, hypothesis_id)

    def _peek_next_hypothesis(self) -> Optional[Hypothesis]:
        """Peek at the next hypothesis without popping."""
        self._check_all_unblocks()

        if not self.pending_queue:
            return None

        return self.tree.get(self.pending_queue[-1])

    # === Query Methods ===

    def get_statistics(self) -> dict:
        """Get statistics about the current state."""
        hypotheses = list(self.tree.hypotheses.values())

        return {
            "total": len(hypotheses),
            "pending": sum(1 for h in hypotheses if h.status == HypothesisStatus.PENDING),
            "in_progress": sum(1 for h in hypotheses if h.status == HypothesisStatus.IN_PROGRESS),
            "completed": sum(1 for h in hypotheses if h.status == HypothesisStatus.COMPLETED),
            "blocked": sum(1 for h in hypotheses if h.status == HypothesisStatus.BLOCKED),
            "dead_end": sum(1 for h in hypotheses if h.status == HypothesisStatus.DEAD_END),
            "vulnerabilities": sum(1 for h in hypotheses if h.result == HypothesisResult.VULNERABLE),
            "queue_size": len(self.pending_queue),
            "blocked_count": len(self.blocked_list),
            "outputs_available": len(self.outputs_registry),
        }

    def get_vulnerabilities(self) -> list[Hypothesis]:
        """Get all hypotheses that found vulnerabilities."""
        return self.tree.get_vulnerabilities()

    def get_blocked_hypotheses(self) -> list[Hypothesis]:
        """Get all currently blocked hypotheses."""
        return [
            h for h in self.tree.hypotheses.values()
            if h.status == HypothesisStatus.BLOCKED
        ]

    def is_complete(self) -> bool:
        """Check if exploration is complete."""
        return len(self.pending_queue) == 0 and len(self.blocked_list) == 0

    def to_dict(self) -> dict:
        """Serialize manager state for persistence."""
        return {
            "tree": self.tree.to_dict(),
            "pending_queue": self.pending_queue,
            "blocked_list": [
                {
                    "hypothesis_id": b.hypothesis_id,
                    "waiting_for": b.waiting_for,
                    "blocked_at": b.blocked_at.isoformat(),
                }
                for b in self.blocked_list
            ],
            "outputs_registry": self.outputs_registry,
            "pending_outputs": self.pending_outputs,
            "current_hypothesis_id": self.current_hypothesis_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HypothesisManager":
        """Deserialize manager state."""
        manager = cls()
        manager.tree = HypothesisTree.from_dict(data.get("tree", {}))
        manager.pending_queue = data.get("pending_queue", [])
        manager.blocked_list = [
            BlockedHypothesis(
                hypothesis_id=b["hypothesis_id"],
                waiting_for=b["waiting_for"],
                blocked_at=datetime.fromisoformat(b["blocked_at"]),
            )
            for b in data.get("blocked_list", [])
        ]
        manager.outputs_registry = data.get("outputs_registry", {})
        manager.pending_outputs = data.get("pending_outputs", {})
        manager.current_hypothesis_id = data.get("current_hypothesis_id")
        return manager


def create_manager(initial_hypotheses: list[Hypothesis] = None) -> HypothesisManager:
    """
    Factory function to create a HypothesisManager.

    Args:
        initial_hypotheses: Optional list of initial hypotheses to seed

    Returns:
        A new HypothesisManager instance
    """
    manager = HypothesisManager()

    if initial_hypotheses:
        for hypothesis in initial_hypotheses:
            manager.add_hypothesis(hypothesis)

    return manager
