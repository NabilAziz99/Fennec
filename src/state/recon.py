"""
Reconnaissance data structures.

Stores information gathered during the initial recon phase.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class TechnologyType(str, Enum):
    """Types of technologies detected."""
    FRAMEWORK = "framework"
    LANGUAGE = "language"
    DATABASE = "database"
    SERVER = "server"
    CMS = "cms"
    LIBRARY = "library"
    AUTH = "auth"
    WAF = "waf"
    OTHER = "other"


def _safe_technology_type(value: str) -> TechnologyType:
    """Safely convert string to TechnologyType, defaulting to OTHER for unknown values."""
    try:
        return TechnologyType(value.lower())
    except (ValueError, AttributeError):
        return TechnologyType.OTHER


class ComponentType(str, Enum):
    """Types of components in an application inventory."""
    PLUGIN = "plugin"
    THEME = "theme"
    MODULE = "module"
    LIBRARY = "library"
    SERVICE = "service"
    FRAMEWORK = "framework"
    CMS = "cms"
    SERVER = "server"  # Added to handle server components
    OTHER = "other"


def _safe_component_type(value: str) -> ComponentType:
    """Safely convert string to ComponentType, defaulting to OTHER for unknown values."""
    try:
        return ComponentType(value.lower())
    except (ValueError, AttributeError):
        return ComponentType.OTHER


@dataclass
class Technology:
    """A detected technology."""
    name: str
    version: Optional[str] = None
    type: TechnologyType = TechnologyType.OTHER
    confidence: float = 0.5  # 0.0 to 1.0


@dataclass
class Component:
    """A discovered component (plugin/theme/module/etc.)."""
    name: str
    type: ComponentType = ComponentType.OTHER
    version: Optional[str] = None
    location: Optional[str] = None  # path or URL
    evidence_refs: list[str] = field(default_factory=list)
    confidence: float = 0.5  # 0.0 to 1.0
    notes: str = ""


@dataclass
class CanonicalAccess:
    """Canonical access tuple for consistent web tool usage."""
    scheme: str
    host: str
    port: Optional[int] = None
    base_path: Optional[str] = None
    host_header: Optional[str] = None
    justification: str = ""
    evidence_ref: Optional[str] = None


@dataclass
class Endpoint:
    """A discovered endpoint (schema-improvements.md §5)."""
    path: str
    method: str = "GET"
    parameters: list[str] = field(default_factory=list)
    status_code: Optional[int] = None
    content_type: Optional[str] = None
    redirect_to: Optional[str] = None
    title: Optional[str] = None
    discovered_by: Optional[str] = None
    params: Optional[list[dict]] = None  # parameter `location` (query, path, header, cookie, body)
    auth_scheme: Optional[str] = None  # not just auth_required
    auth_required: bool = False
    response_type: str = ""  # json, html, xml, etc.
    notes: str = ""


@dataclass
class EntryPoint:
    """A potential entry point for attacks."""
    location: str  # URL path or parameter
    type: str  # "form", "api", "header", "cookie", "file_upload", etc.
    input_type: str = ""  # "text", "number", "file", etc.
    validation_observed: str = ""  # What validation was observed
    notes: str = ""
@dataclass
class VulnCandidate:
    """A potential vulnerability candidate."""
    cve_id: Optional[str] = None
    title: Optional[str] = None
    component: Optional[str] = None  # e.g. plugin name
    detected_version: Optional[str] = None
    affected_range: Optional[str] = None
    preconditions: Optional[str] = None  # e.g., auth/method/headers required
    exploit_paths: list[str] = field(default_factory=list)  # e.g. URLs or API routes
    confidence: float = 0.5
    evidence_refs: list[str] = field(default_factory=list)  # links to proof: GET output, version metadata, etc
@dataclass
class EvidenceItem:
    """
    Evidence/provenance for findings.
    """
    source: str  # Tool used (e.g., "nmap", "httpx", etc.)
    artifact: str  # URL, command, or related artifact
    timestamp: Optional[datetime] = None
    status_code: Optional[int] = None
    key_headers: Optional[dict[str, str]] = field(default_factory=dict)
    body_snippet_hash: Optional[str] = None  # or short extract

@dataclass
class ReconData:
    """
    All reconnaissance data gathered about the target.

    This is populated by the Recon Agent and consumed by
    the Hypothesis Agent to form attack theories.
    """
    target_url: str

    # Basic info
    ip_address: Optional[str] = None
    ports_open: list[int] = field(default_factory=list)
    canonical_access: Optional[CanonicalAccess] = None

    # Technologies detected
    technologies: list[Technology] = field(default_factory=list)

    # Component inventory (plugins, themes, modules, etc.)
    components: list[Component] = field(default_factory=list)

    # Endpoints discovered
    endpoints: list[Endpoint] = field(default_factory=list)

    # Entry points for attacks
    entry_points: list[EntryPoint] = field(default_factory=list)

    # Authentication info
    auth_type: Optional[str] = None  # "jwt", "session", "basic", "oauth", etc.
    login_endpoint: Optional[str] = None
    registration_available: bool = False
    default_credentials_found: list[dict] = field(default_factory=list)

    # Additional observations
    headers_of_interest: dict[str, str] = field(default_factory=dict)
    cookies_observed: list[str] = field(default_factory=list)


    vulnerability_candidates: list[VulnCandidate] = field(default_factory=list)
    evidence_items: list[EvidenceItem] = field(default_factory=list)

    # Raw notes from recon
    summary: str = ""
    priority_targets: list[str] = field(default_factory=list)
    key_findings: list[str] = field(default_factory=list)
    # Metadata
    recon_started: datetime = field(default_factory=datetime.utcnow)
    recon_completed: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for state storage."""
        return {
            "target_url": self.target_url,
            "ip_address": self.ip_address,
            "ports_open": self.ports_open,
            "canonical_access": (
                {
                    "scheme": self.canonical_access.scheme,
                    "host": self.canonical_access.host,
                    "port": self.canonical_access.port,
                    "base_path": self.canonical_access.base_path,
                    "host_header": self.canonical_access.host_header,
                    "justification": self.canonical_access.justification,
                    "evidence_ref": self.canonical_access.evidence_ref,
                }
                if self.canonical_access
                else None
            ),
            "technologies": [
                {"name": t.name, "version": t.version, "type": t.type.value, "confidence": t.confidence}
                for t in self.technologies
            ],
            "components": [
                {
                    "name": c.name,
                    "type": c.type.value,
                    "version": c.version,
                    "location": c.location,
                    "evidence_refs": c.evidence_refs,
                    "confidence": c.confidence,
                    "notes": c.notes,
                }
                for c in self.components
            ],
            "endpoints": [
                {
                    "path": e.path,
                    "method": e.method,
                    "parameters": e.parameters,
                    "status_code": e.status_code,
                    "content_type": e.content_type,
                    "redirect_to": e.redirect_to,
                    "title": e.title,
                    "discovered_by": e.discovered_by,
                    "params": e.params,
                    "auth_scheme": e.auth_scheme,
                    "auth_required": e.auth_required,
                    "response_type": e.response_type,
                    "notes": e.notes,
                }
                for e in self.endpoints
            ],
            "entry_points": [
                {"location": ep.location, "type": ep.type, "input_type": ep.input_type,
                 "validation_observed": ep.validation_observed, "notes": ep.notes}
                for ep in self.entry_points
            ],
            "auth_type": self.auth_type,
            "login_endpoint": self.login_endpoint,
            "registration_available": self.registration_available,
            "default_credentials_found": self.default_credentials_found,
            "headers_of_interest": self.headers_of_interest,
            "cookies_observed": self.cookies_observed,
            "summary": self.summary,
            "priority_targets": self.priority_targets,
            "vulnerability_candidates": [
                {"cve_id": vc.cve_id, "title": vc.title, "component": vc.component, "detected_version": vc.detected_version, "affected_range": vc.affected_range, "preconditions": vc.preconditions, "exploit_paths": vc.exploit_paths, "confidence": vc.confidence, "evidence_refs": vc.evidence_refs}
                for vc in self.vulnerability_candidates
            ],
            "evidence_items": [
                {"source": ei.source, "artifact": ei.artifact, "timestamp": ei.timestamp.isoformat() if ei.timestamp else None, "status_code": ei.status_code, "key_headers": ei.key_headers, "body_snippet_hash": ei.body_snippet_hash}
                for ei in self.evidence_items
            ],
            "key_findings": self.key_findings,
            "recon_started": self.recon_started.isoformat() if self.recon_started else None,
            "recon_completed": self.recon_completed.isoformat() if self.recon_completed else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReconData":
        """Create from dictionary."""
        recon = cls(target_url=data["target_url"])
        recon.ip_address = data.get("ip_address")
        recon.ports_open = data.get("ports_open", [])
        if data.get("canonical_access"):
            canonical = data["canonical_access"]
            recon.canonical_access = CanonicalAccess(
                scheme=canonical.get("scheme", ""),
                host=canonical.get("host", ""),
                port=canonical.get("port"),
                base_path=canonical.get("base_path"),
                host_header=canonical.get("host_header"),
                justification=canonical.get("justification", ""),
                evidence_ref=canonical.get("evidence_ref"),
            )
        recon.technologies = [
            Technology(
                name=t["name"],
                version=t.get("version"),
                type=_safe_technology_type(t.get("type", "other")),
                confidence=t.get("confidence", 0.5)
            )
            for t in data.get("technologies", [])
        ]
        recon.components = [
            Component(
                name=c["name"],
                type=_safe_component_type(c.get("type", "other")),
                version=c.get("version"),
                location=c.get("location"),
                evidence_refs=c.get("evidence_refs", []),
                confidence=c.get("confidence", 0.5),
                notes=c.get("notes", ""),
            )
            for c in data.get("components", [])
        ]
        recon.endpoints = [
            Endpoint(
                path=e["path"],
                method=e.get("method", "GET"),
                parameters=e.get("parameters", []),
                status_code=e.get("status_code"),
                content_type=e.get("content_type"),
                redirect_to=e.get("redirect_to"),
                title=e.get("title"),
                discovered_by=e.get("discovered_by"),
                params=e.get("params"),
                auth_scheme=e.get("auth_scheme"),
                auth_required=e.get("auth_required", False),
                response_type=e.get("response_type", ""),
                notes=e.get("notes", "")
            )
            for e in data.get("endpoints", [])
        ]
        recon.entry_points = [
            EntryPoint(
                location=ep["location"],
                type=ep["type"],
                input_type=ep.get("input_type", ""),
                validation_observed=ep.get("validation_observed", ""),
                notes=ep.get("notes", "")
            )
            for ep in data.get("entry_points", [])
        ]
        recon.auth_type = data.get("auth_type")
        recon.login_endpoint = data.get("login_endpoint")
        recon.registration_available = data.get("registration_available", False)
        recon.default_credentials_found = data.get("default_credentials_found", [])
        recon.headers_of_interest = data.get("headers_of_interest", {})
        recon.cookies_observed = data.get("cookies_observed", [])
        recon.summary = data.get("summary", "")
        recon.priority_targets = data.get("priority_targets", [])
        recon.vulnerability_candidates = [
            VulnCandidate(
                cve_id=vc.get("cve_id"),
                title=vc.get("title"),
                component=vc.get("component"),
                detected_version=vc.get("detected_version"),
                affected_range=vc.get("affected_range"),
                preconditions=vc.get("preconditions"),
                exploit_paths=vc.get("exploit_paths", []),
                confidence=vc.get("confidence", 0.5),
                evidence_refs=vc.get("evidence_refs", []),
            )
            for vc in data.get("vulnerability_candidates", [])
        ]
        recon.evidence_items = [
            EvidenceItem(
                source=ei.get("source", ""),
                artifact=ei.get("artifact", ""),
                timestamp=datetime.fromisoformat(ei["timestamp"]) if ei.get("timestamp") else None,
                status_code=ei.get("status_code"),
                key_headers=ei.get("key_headers", {}),
                body_snippet_hash=ei.get("body_snippet_hash"),
            )
            for ei in data.get("evidence_items", [])
        ]
        recon.key_findings = data.get("key_findings", [])
        recon.notes = data.get("notes", [])

        if data.get("recon_started"):
            recon.recon_started = datetime.fromisoformat(data["recon_started"])
        if data.get("recon_completed"):
            recon.recon_completed = datetime.fromisoformat(data["recon_completed"])

        return recon

    def get_summary(self) -> str:
        """Get a text summary for prompt injection."""
        lines = [f"## Recon Summary for {self.target_url}"]

        if self.canonical_access:
            canonical = self.canonical_access
            port = f":{canonical.port}" if canonical.port else ""
            base_path = canonical.base_path or ""
            host_header = f" (Host: {canonical.host_header})" if canonical.host_header else ""
            lines.append("\n### Canonical Access")
            lines.append(f"- {canonical.scheme}://{canonical.host}{port}{base_path}{host_header}")
            if canonical.justification:
                lines.append(f"- Reason: {canonical.justification}")
            if canonical.evidence_ref:
                lines.append(f"- Evidence: {canonical.evidence_ref}")

        if self.technologies:
            lines.append("\n### Technologies Detected")
            for t in self.technologies:
                ver = f" v{t.version}" if t.version else ""
                lines.append(f"- {t.name}{ver} ({t.type.value})")

        if self.components:
            lines.append(f"\n### Components ({len(self.components)})")
            for c in self.components[:10]:
                ver = f" v{c.version}" if c.version else ""
                lines.append(f"- {c.name}{ver} ({c.type.value})")
            if len(self.components) > 10:
                lines.append(f"  ... and {len(self.components) - 10} more")

        if self.endpoints:
            lines.append(f"\n### Endpoints Discovered ({len(self.endpoints)})")
            for e in self.endpoints[:10]:  # Limit to 10
                auth = " [AUTH]" if e.auth_required else ""
                params = f" params: {e.parameters}" if e.parameters else ""
                lines.append(f"- {e.method} {e.path}{auth}{params}")
            if len(self.endpoints) > 10:
                lines.append(f"  ... and {len(self.endpoints) - 10} more")

        if self.entry_points:
            lines.append(f"\n### Entry Points ({len(self.entry_points)})")
            for ep in self.entry_points[:10]:
                lines.append(f"- [{ep.type}] {ep.location}")
            if len(self.entry_points) > 10:
                lines.append(f"  ... and {len(self.entry_points) - 10} more")

        if self.auth_type:
            lines.append(f"\n### Authentication: {self.auth_type}")
            if self.login_endpoint:
                lines.append(f"- Login: {self.login_endpoint}")
            if self.default_credentials_found:
                lines.append(f"- Default credentials found: {len(self.default_credentials_found)}")

        if self.summary:
            lines.append("\n### Recon Summary")
            lines.append(self.summary)

        if self.priority_targets:
            lines.append("\n### Priority Targets")
            for target in self.priority_targets[:10]:
                lines.append(f"- {target}")
            if len(self.priority_targets) > 10:
                lines.append(f"  ... and {len(self.priority_targets) - 10} more")

        if self.key_findings:
            lines.append("\n### Key Findings")
            for finding in self.key_findings:
                lines.append(f"- {finding}")

        return "\n".join(lines)
