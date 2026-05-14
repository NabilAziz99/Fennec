"""
Correlation data structures.

Stores findings and correlations discovered during testing.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from .hypothesis import Severity

# Backward-compatible alias — all new code should use ``Severity`` directly.
FindingSeverity = Severity


class FindingStatus(str, Enum):
    """Status of a finding."""
    CONFIRMED = "confirmed"
    POTENTIAL = "potential"
    FALSE_POSITIVE = "false_positive"
    NEEDS_VERIFICATION = "needs_verification"


@dataclass
class Finding:
    """A security finding from testing."""
    id: str
    title: str
    description: str
    severity: FindingSeverity = FindingSeverity.INFO
    status: FindingStatus = FindingStatus.POTENTIAL

    # Where it was found
    location: str = ""  # URL/endpoint
    parameter: str = ""  # Affected parameter

    # Evidence
    evidence: str = ""
    reproduction_steps: list[str] = field(default_factory=list)

    # Classification
    vulnerability_type: str = ""  # sqli, xss, idor, etc.
    cwe_id: Optional[str] = None

    # Linking
    related_findings: list[str] = field(default_factory=list)  # IDs of related findings
    hypothesis_id: Optional[str] = None  # Which hypothesis led to this

    # Metadata
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    discovered_by: str = ""  # Agent that found it

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "status": self.status.value,
            "location": self.location,
            "parameter": self.parameter,
            "evidence": self.evidence,
            "reproduction_steps": self.reproduction_steps,
            "vulnerability_type": self.vulnerability_type,
            "cwe_id": self.cwe_id,
            "related_findings": self.related_findings,
            "hypothesis_id": self.hypothesis_id,
            "discovered_at": self.discovered_at.isoformat(),
            "discovered_by": self.discovered_by,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Finding":
        finding = cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
        )
        finding.severity = FindingSeverity(data.get("severity", "info"))
        finding.status = FindingStatus(data.get("status", "potential"))
        finding.location = data.get("location", "")
        finding.parameter = data.get("parameter", "")
        finding.evidence = data.get("evidence", "")
        finding.reproduction_steps = data.get("reproduction_steps", [])
        finding.vulnerability_type = data.get("vulnerability_type", "")
        finding.cwe_id = data.get("cwe_id")
        finding.related_findings = data.get("related_findings", [])
        finding.hypothesis_id = data.get("hypothesis_id")
        if data.get("discovered_at"):
            finding.discovered_at = datetime.fromisoformat(data["discovered_at"])
        finding.discovered_by = data.get("discovered_by", "")
        return finding


@dataclass
class Correlation:
    """A correlation between multiple findings."""
    id: str
    title: str
    description: str

    # The findings being correlated
    finding_ids: list[str] = field(default_factory=list)

    # What the correlation suggests
    attack_chain: str = ""  # Description of potential attack chain
    escalation_potential: str = ""  # What this could lead to

    # Actions suggested
    new_recon_targets: list[str] = field(default_factory=list)  # Areas needing more recon
    new_hypotheses: list[dict] = field(default_factory=list)  # New attack theories

    # Metadata
    confidence: float = 0.5  # 0.0 to 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "finding_ids": self.finding_ids,
            "attack_chain": self.attack_chain,
            "escalation_potential": self.escalation_potential,
            "new_recon_targets": self.new_recon_targets,
            "new_hypotheses": self.new_hypotheses,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Correlation":
        corr = cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
        )
        corr.finding_ids = data.get("finding_ids", [])
        corr.attack_chain = data.get("attack_chain", "")
        corr.escalation_potential = data.get("escalation_potential", "")
        corr.new_recon_targets = data.get("new_recon_targets", [])
        corr.new_hypotheses = data.get("new_hypotheses", [])
        corr.confidence = data.get("confidence", 0.5)
        if data.get("created_at"):
            corr.created_at = datetime.fromisoformat(data["created_at"])
        return corr


@dataclass
class CorrelationStore:
    """Store for all findings and correlations."""
    findings: dict[str, Finding] = field(default_factory=dict)  # id -> Finding
    correlations: dict[str, Correlation] = field(default_factory=dict)  # id -> Correlation

    def add_finding(self, finding: Finding) -> None:
        """Add a finding."""
        self.findings[finding.id] = finding

    def add_correlation(self, correlation: Correlation) -> None:
        """Add a correlation."""
        self.correlations[correlation.id] = correlation

    def get_findings_by_type(self, vuln_type: str) -> list[Finding]:
        """Get all findings of a specific vulnerability type."""
        return [f for f in self.findings.values() if f.vulnerability_type == vuln_type]

    def get_findings_by_location(self, location: str) -> list[Finding]:
        """Get all findings at a specific location."""
        return [f for f in self.findings.values() if location in f.location]

    def get_confirmed_findings(self) -> list[Finding]:
        """Get all confirmed findings."""
        return [f for f in self.findings.values() if f.status == FindingStatus.CONFIRMED]

    def get_unprocessed_correlations(self) -> list[Correlation]:
        """Get correlations that suggest new actions."""
        return [
            c for c in self.correlations.values()
            if c.new_recon_targets or c.new_hypotheses
        ]

    def to_dict(self) -> dict:
        return {
            "findings": {k: v.to_dict() for k, v in self.findings.items()},
            "correlations": {k: v.to_dict() for k, v in self.correlations.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CorrelationStore":
        store = cls()
        for k, v in data.get("findings", {}).items():
            store.findings[k] = Finding.from_dict(v)
        for k, v in data.get("correlations", {}).items():
            store.correlations[k] = Correlation.from_dict(v)
        return store

    def get_summary(self) -> str:
        """Get a text summary for prompt injection."""
        lines = ["## Findings Summary"]

        # Count by severity
        by_severity = {}
        for f in self.findings.values():
            by_severity[f.severity.value] = by_severity.get(f.severity.value, 0) + 1

        if by_severity:
            lines.append(f"\n**Total Findings:** {len(self.findings)}")
            for sev in ["critical", "high", "medium", "low", "info"]:
                if sev in by_severity:
                    lines.append(f"- {sev.upper()}: {by_severity[sev]}")

        # List confirmed findings
        confirmed = self.get_confirmed_findings()
        if confirmed:
            lines.append("\n### Confirmed Vulnerabilities")
            for f in confirmed[:10]:
                lines.append(f"- [{f.severity.value.upper()}] {f.title} at {f.location}")

        # List correlations
        if self.correlations:
            lines.append(f"\n### Correlations Found: {len(self.correlations)}")
            for c in list(self.correlations.values())[:5]:
                lines.append(f"- {c.title}")
                if c.attack_chain:
                    lines.append(f"  Chain: {c.attack_chain[:100]}")

        return "\n".join(lines)
