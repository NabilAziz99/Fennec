"""
Pydantic schemas for hypothesis-based tools.

These schemas define the structured inputs for the report_result tool
that agents use to report their findings back to the orchestrator.
"""

from typing import Optional
from pydantic import BaseModel, Field


class NewHypothesisInput(BaseModel):
    """Schema for creating a new child hypothesis."""

    title: str = Field(
        description="Short title for the new hypothesis (e.g., 'Test IDOR on /api/users')"
    )
    description: str = Field(
        default="",
        description="Detailed description of what to test and why"
    )
    required_agent: str = Field(
        default="pentester",
        description="Agent type needed: pentester, coder, or researcher"
    )
    skills: list[str] = Field(
        default_factory=list,
        description="Skills to inject (e.g., ['sql_injection', 'authentication'])"
    )
    priority: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Priority 0.0-1.0, higher = more important to explore"
    )
    expected_outputs: list[str] = Field(
        default_factory=list,
        description="What this hypothesis might produce (e.g., ['admin_session', 'api_key'])"
    )


class ReportResultInput(BaseModel):
    """
    Schema for the report_result tool.

    Agents call this to report their findings after processing a hypothesis.
    This structured output enables the orchestrator to update the hypothesis
    tree and make routing decisions.
    """

    status: str = Field(
        description=(
            "Exploration status:\n"
            "- 'completed': Hypothesis fully explored, has a definitive result\n"
            "- 'needs_info': Agent is stuck, needs something from another hypothesis\n"
            "- 'dead_end': Cannot proceed, no viable path forward"
        )
    )

    result: Optional[str] = Field(
        default=None,
        description=(
            "Only if status='completed'. The outcome:\n"
            "- 'vulnerable': Security issue confirmed\n"
            "- 'safe': No vulnerability found\n"
            "- 'inconclusive': Could not determine"
        )
    )

    severity: Optional[str] = Field(
        default=None,
        description=(
            "Only if result='vulnerable'. Severity level:\n"
            "- 'critical': Immediate risk, full compromise possible\n"
            "- 'high': Significant risk, major impact\n"
            "- 'medium': Moderate risk, limited impact\n"
            "- 'low': Minor risk, minimal impact\n"
            "- 'info': Informational finding"
        )
    )

    outputs: list[str] = Field(
        default_factory=list,
        description=(
            "What this hypothesis produced that other hypotheses might need. "
            "Examples: ['admin_credentials', 'session_token', 'internal_api_url']"
        )
    )

    findings: list[str] = Field(
        default_factory=list,
        description=(
            "Human-readable description of what was discovered. "
            "Examples: ['Time-based SQLi confirmed on /login', 'Extracted 500 user records']"
        )
    )

    internal_steps: list[str] = Field(
        default_factory=list,
        description=(
            "Log of what you tried internally (for debugging). "
            "Examples: ['Tried error-based SQLi: blocked', 'Tried time-based: SUCCESS']"
        )
    )

    new_hypotheses: list[NewHypothesisInput] = Field(
        default_factory=list,
        description=(
            "New attack paths to explore. Only create when:\n"
            "1. A DIFFERENT agent is needed for the next step\n"
            "2. A completely NEW attack surface was discovered\n"
            "Do NOT create hypotheses for things you can handle internally!"
        )
    )

    needs: list[str] = Field(
        default_factory=list,
        description=(
            "Only if status='needs_info'. What you need but don't have. "
            "Examples: ['payment_token', 'admin_session', 'internal_api_access']"
        )
    )

    error: Optional[str] = Field(
        default=None,
        description="Only if status='dead_end'. Explanation of why no progress is possible."
    )
