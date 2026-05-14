"""
Hypothesis data structures for the penetration testing workflow.

A hypothesis represents a testable security assumption that an agent explores.
Hypotheses form a tree structure, enabling DFS traversal with priority-based ordering.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid


class HypothesisStatus(str, Enum):
    """Status of a hypothesis in the exploration workflow."""
    PENDING = "pending"           # Waiting to be processed
    IN_PROGRESS = "in_progress"   # Currently being explored
    COMPLETED = "completed"       # Exploration finished
    BLOCKED = "blocked"           # Waiting for another hypothesis
    DEAD_END = "dead_end"         # Cannot be explored further


class HypothesisResult(str, Enum):
    """Result of a completed hypothesis."""
    VULNERABLE = "vulnerable"     # Security issue confirmed
    SAFE = "safe"                 # No vulnerability found
    INCONCLUSIVE = "inconclusive" # Could not determine


class Severity(str, Enum):
    """Severity level of a discovered vulnerability."""
    CRITICAL = "critical"  # Immediate risk, full compromise possible
    HIGH = "high"          # Significant risk, major impact
    MEDIUM = "medium"      # Moderate risk, limited impact
    LOW = "low"            # Minor risk, minimal impact
    INFO = "info"          # Informational finding


class AgentRole(str, Enum):
    """Hypothesis-level role tags indicating which agent should handle a hypothesis.

    Unlike :class:`~src.state.graph_state.AgentType` (which enumerates
    actual LangGraph *nodes*), ``AgentRole`` includes ``CODER`` — a sub-agent
    invoked by the pentester rather than a standalone graph node.
    """
    ORCHESTRATOR = "orchestrator"
    PENTESTER = "pentester"
    CODER = "coder"


@dataclass
class Hypothesis:
    """
    A hypothesis to test during penetration testing.

    Hypotheses form a tree structure where:
    - Root hypotheses are initial attack vectors (e.g., "Test SQLi on /login")
    - Child hypotheses branch from findings (e.g., "Extract admin credentials")
    - Each hypothesis is assigned to a specific agent with relevant skills

    The hypothesis tree is traversed using DFS with priority ordering,
    ensuring the most promising paths are explored first.
    """

    # Unique identifier
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # === Tree Structure ===
    parent_id: Optional[str] = None
    children_ids: list[str] = field(default_factory=list)

    # === Description ===
    title: str = ""
    description: str = ""

    # === Routing ===
    # Which agent should handle this hypothesis
    required_agent: AgentRole = AgentRole.PENTESTER
    

    # Skills to inject into the agent's prompt (e.g., ["sql_injection", "authentication_jwt"])
    skills: list[str] = field(default_factory=list)

    # OWASP Top 10 category code (e.g. "A01", "A03")
    owasp_category: str = ""

    # === Status Tracking ===
    status: HypothesisStatus = HypothesisStatus.PENDING
    result: Optional[HypothesisResult] = None
    severity: Optional[Severity] = None

    # === Priority ===
    # 0.0 - 1.0, higher = more promising, explored first in DFS
    priority: float = 0.5

    # === Dependencies ===
    # ID of hypothesis we're waiting for (if blocked)
    blocked_by: Optional[str] = None
    # What output we need from the blocking hypothesis
    waiting_for: Optional[str] = None

    # === Outputs ===
    # What this hypothesis might produce (declared upfront for dependency resolution)
    expected_outputs: list[str] = field(default_factory=list)

    # === Timestamps ===
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # === UI Properties ===
    @property
    def color(self) -> str:
        """Color code for UI visualization."""
        if self.result == HypothesisResult.VULNERABLE:
            return {
                Severity.CRITICAL: "red",
                Severity.HIGH: "orange",
                Severity.MEDIUM: "yellow",
                Severity.LOW: "blue",
                Severity.INFO: "gray",
            }.get(self.severity, "red")
        elif self.result == HypothesisResult.SAFE:
            return "green"
        elif self.status == HypothesisStatus.BLOCKED:
            return "purple"
        elif self.status == HypothesisStatus.DEAD_END:
            return "gray"
        elif self.status == HypothesisStatus.IN_PROGRESS:
            return "cyan"
        return "white"  # pending

    @property
    def depth(self) -> int:
        """Depth in the tree (0 for root hypotheses)."""
        # This would need the full tree to calculate properly
        # For now, return 0 if no parent
        return 0 if self.parent_id is None else 1

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "title": self.title,
            "description": self.description,
            "required_agent": self.required_agent.value,
            "skills": self.skills,
            "owasp_category": self.owasp_category,
            "status": self.status.value,
            "result": self.result.value if self.result else None,
            "severity": self.severity.value if self.severity else None,
            "priority": self.priority,
            "blocked_by": self.blocked_by,
            "waiting_for": self.waiting_for,
            "expected_outputs": self.expected_outputs,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "color": self.color,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Hypothesis":
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            parent_id=data.get("parent_id"),
            children_ids=data.get("children_ids", []),
            title=data.get("title", ""),
            description=data.get("description", ""),
            required_agent=AgentRole(data.get("required_agent", "pentester")),
            skills=data.get("skills", []),
            owasp_category=data.get("owasp_category", ""),
            status=HypothesisStatus(data.get("status", "pending")),
            result=HypothesisResult(data["result"]) if data.get("result") else None,
            severity=Severity(data["severity"]) if data.get("severity") else None,
            priority=data.get("priority", 0.5),
            blocked_by=data.get("blocked_by"),
            waiting_for=data.get("waiting_for"),
            expected_outputs=data.get("expected_outputs", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(timezone.utc),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )


@dataclass
class HypothesisTree:
    """
    Container for the full hypothesis tree.

    Provides helper methods for tree operations while keeping
    the actual data in simple dict format for LangGraph state.
    """
    hypotheses: dict[str, Hypothesis] = field(default_factory=dict)

    def add(self, hypothesis: Hypothesis) -> None:
        """Add a hypothesis to the tree."""
        self.hypotheses[hypothesis.id] = hypothesis

        # Update parent's children list
        if hypothesis.parent_id and hypothesis.parent_id in self.hypotheses:
            parent = self.hypotheses[hypothesis.parent_id]
            if hypothesis.id not in parent.children_ids:
                parent.children_ids.append(hypothesis.id)

    def get(self, hypothesis_id: str) -> Optional[Hypothesis]:
        """Get a hypothesis by ID."""
        return self.hypotheses.get(hypothesis_id)

    def get_children(self, hypothesis_id: str) -> list[Hypothesis]:
        """Get all children of a hypothesis."""
        hypothesis = self.hypotheses.get(hypothesis_id)
        if not hypothesis:
            return []
        return [self.hypotheses[cid] for cid in hypothesis.children_ids if cid in self.hypotheses]

    def get_root_hypotheses(self) -> list[Hypothesis]:
        """Get all root hypotheses (no parent)."""
        return [h for h in self.hypotheses.values() if h.parent_id is None]

    def get_by_status(self, status: HypothesisStatus) -> list[Hypothesis]:
        """Get all hypotheses with a specific status."""
        return [h for h in self.hypotheses.values() if h.status == status]

    def get_vulnerabilities(self) -> list[Hypothesis]:
        """Get all hypotheses that found vulnerabilities."""
        return [h for h in self.hypotheses.values() if h.result == HypothesisResult.VULNERABLE]

    def to_dict(self) -> dict[str, dict]:
        """Convert to dictionary for serialization."""
        return {hid: h.to_dict() for hid, h in self.hypotheses.items()}

    @classmethod
    def from_dict(cls, data: dict[str, dict]) -> "HypothesisTree":
        """Create from dictionary."""
        tree = cls()
        for hid, hdata in data.items():
            tree.hypotheses[hid] = Hypothesis.from_dict(hdata)
        return tree
