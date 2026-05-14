"""
Agent result data structures.

Defines the structured output that agents return after processing a hypothesis.
This standardized format enables the orchestrator to make routing decisions
and manage the hypothesis tree.
"""

from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class NewHypothesisData:
    """
    Data for creating a new child hypothesis.

    Agents return this when they discover new attack paths
    that need to be explored.
    """
    title: str
    description: str = ""
    required_agent: str = "pentester"
    skills: list[str] = field(default_factory=list)
    priority: float = 0.5
    expected_outputs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "required_agent": self.required_agent,
            "skills": self.skills,
            "priority": self.priority,
            "expected_outputs": self.expected_outputs,
        }


@dataclass
class AgentResult:
    """
    Structured result from an agent processing a hypothesis.

    This is the contract between agents and the orchestrator:
    - Agents return AgentResult after processing
    - Orchestrator uses this to update the hypothesis tree and routing

    Status meanings:
    - completed: Hypothesis fully explored, has a definitive result
    - needs_info: Agent is stuck, needs something from another hypothesis
    - dead_end: Cannot proceed, no viable path forward
    """

    # === Status ===
    status: Literal["completed", "needs_info", "dead_end"]

    # === Result (only if status == "completed") ===
    # Whether a vulnerability was found
    result: Optional[Literal["vulnerable", "safe", "inconclusive"]] = None

    # Severity of the vulnerability (only if result == "vulnerable")
    severity: Optional[Literal["critical", "high", "medium", "low", "info"]] = None

    # === Outputs ===
    # What this hypothesis produced that other hypotheses might need
    # Examples: ["admin_credentials", "session_tokens", "internal_api_url"]
    outputs: list[str] = field(default_factory=list)

    # === Findings ===
    # Human-readable description of what was discovered
    findings: list[str] = field(default_factory=list)

    # === Internal Steps ===
    # Log of what the agent tried internally (for debugging/UI)
    # Examples: ["Tried error-based SQLi: blocked", "Tried time-based: SUCCESS"]
    internal_steps: list[str] = field(default_factory=list)

    # === New Hypotheses (analyst only) ===
    # Child hypotheses to add to the tree
    # Only the analyst creates these via the report_result tool
    new_hypotheses: list[NewHypothesisData] = field(default_factory=list)

    # === Suggested Followups (pentester → analyst) ===
    # Text hints about new attack paths the pentester noticed during testing.
    # The analyst reads these and decides whether to create hypotheses.
    suggested_followups: list[str] = field(default_factory=list)

    # === Needs (only if status == "needs_info") ===
    # What the agent needs but doesn't have
    # Examples: ["payment_token", "admin_session", "internal_api_access"]
    needs: list[str] = field(default_factory=list)

    # === Error (only if status == "dead_end") ===
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for logging/serialization."""
        return {
            "status": self.status,
            "result": self.result,
            "severity": self.severity,
            "outputs": self.outputs,
            "findings": self.findings,
            "internal_steps": self.internal_steps,
            "new_hypotheses": [nh.to_dict() for nh in self.new_hypotheses],
            "suggested_followups": self.suggested_followups,
            "needs": self.needs,
            "error": self.error,
        }

    @classmethod
    def completed(
        cls,
        result: Literal["vulnerable", "safe", "inconclusive"],
        findings: list[str],
        outputs: list[str] = None,
        severity: Optional[Literal["critical", "high", "medium", "low", "info"]] = None,
        new_hypotheses: list[NewHypothesisData] = None,
        internal_steps: list[str] = None,
    ) -> "AgentResult":
        """Factory for a completed result."""
        return cls(
            status="completed",
            result=result,
            severity=severity,
            outputs=outputs or [],
            findings=findings,
            internal_steps=internal_steps or [],
            new_hypotheses=new_hypotheses or [],
        )

    @classmethod
    def needs_info(
        cls,
        needs: list[str],
        findings: list[str] = None,
        internal_steps: list[str] = None,
    ) -> "AgentResult":
        """Factory for a needs_info result."""
        return cls(
            status="needs_info",
            needs=needs,
            findings=findings or [],
            internal_steps=internal_steps or [],
        )

    @classmethod
    def dead_end(
        cls,
        error: str,
        findings: list[str] = None,
        internal_steps: list[str] = None,
    ) -> "AgentResult":
        """Factory for a dead_end result."""
        return cls(
            status="dead_end",
            error=error,
            findings=findings or [],
            internal_steps=internal_steps or [],
        )
