"""
Structured output schema for the analyst agent.
"""

from typing import Optional

from pydantic import BaseModel, Field


class HypothesisData(BaseModel):
    """A hypothesis created by the analyst."""
    title: str = Field(description="Brief title for the hypothesis")
    description: str = Field(description="Detailed description of the attack theory")
    skills: list[str] = Field(default_factory=list, description="Relevant skills (e.g. sql_injection, xss)")
    priority: float = Field(default=0.5, ge=0.0, le=1.0, description="Priority 0.0-1.0")
    expected_outputs: list[str] = Field(default_factory=list, description="What we expect to find")
    location: str = Field(default="", description="Specific endpoint or parameter")
    attack_vector: str = Field(default="", description="Type of attack (sqli, xss, idor, etc.)")
    related_recon_findings: list[str] = Field(default_factory=list, description="Related recon findings")


# class CorrelationData(BaseModel):
#     """A correlation between findings identified by the analyst."""
#     title: str = Field(description="Brief title for the correlation")
#     description: str = Field(default="", description="How the findings are related")
#     finding_ids: list[str] = Field(default_factory=list, description="IDs of related findings")
#     attack_chain: str = Field(default="", description="How vulnerabilities chain together")
#     escalation_potential: str = Field(default="", description="Potential for escalation")


class AnalystResult(BaseModel):
    """Structured result from the analyst agent — all analysis in one response."""
    summary: str = Field(
        description="Brief summary of the analysis performed"
    )
    hypotheses: list[HypothesisData] = Field(
        default_factory=list,
        description="New attack hypotheses to add to the tree"
    )
    # correlations: list[CorrelationData] = Field(
    #     default_factory=list,
    #     description="Links between findings (attack chains, patterns)"
    # )
    recon_request: Optional[str] = Field(
        default=None,
        description="Specific recon task to request if more information is needed"
    )
    recon_reason: Optional[str] = Field(
        default=None,
        description="Why additional recon is needed"
    )
