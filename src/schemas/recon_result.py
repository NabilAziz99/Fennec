"""
Structured output schema for the recon agent.
"""

from typing import Optional

from pydantic import BaseModel, Field
try:
    # pydantic v2
    from pydantic import ConfigDict
except Exception:  # pragma: no cover
    ConfigDict = None  # type: ignore


class CanonicalAccessResult(BaseModel):
    """Canonical access tuple — how tools should reach the target."""
    scheme: str = Field(default="http", description="http or https")
    host: str = Field(description="Hostname or IP to connect to")
    port: Optional[int] = Field(default=None, description="Port number if non-standard")
    base_path: Optional[str] = Field(default=None, description="Base path prefix if any")
    host_header: Optional[str] = Field(default=None, description="Host header to send if different from connect host")
    justification: str = Field(default="", description="Why this access tuple was chosen")


class EndpointResult(BaseModel):
    """A discovered endpoint."""
    path: str = Field(description="Endpoint path (e.g. /api/users)")
    method: str = Field(default="GET", description="HTTP method")
    parameters: list[str] = Field(default_factory=list, description="Query or body parameters")
    status_code: Optional[int] = Field(default=None, description="HTTP status code observed")
    content_type: Optional[str] = Field(default=None, description="Content-Type header value")
    redirect_to: Optional[str] = Field(default=None, description="Redirect target if 3xx")
    discovered_by: Optional[str] = Field(default=None, description="Tool that found this (gobuster, curl, etc.)")
    auth_required: bool = Field(default=False, description="Whether auth is required")
    auth_scheme: Optional[str] = Field(default=None, description="Auth scheme (bearer, basic, cookie, etc.)")
    notes: str = Field(default="", description="Additional notes")


class TechnologyResult(BaseModel):
    """A detected technology."""
    name: str = Field(description="Technology name (e.g. Express, React)")
    version: Optional[str] = Field(default=None, description="Version if known")
    type: str = Field(default="other", description="framework, language, database, server, cms, library, auth, other")
    confidence: float = Field(default=0.5, description="Confidence 0.0-1.0")


class ComponentResult(BaseModel):
    """A discovered component (plugin, theme, module, etc.)."""
    name: str = Field(description="Component name")
    type: str = Field(default="other", description="plugin, theme, module, library, service, framework, cms, other")
    version: Optional[str] = Field(default=None, description="Version if known")
    location: Optional[str] = Field(default=None, description="Path or URL where found")
    evidence_refs: list[str] = Field(default_factory=list, description="Evidence references (URLs, command outputs)")
    confidence: float = Field(default=0.5, description="Confidence 0.0-1.0")
    notes: str = Field(default="", description="Additional notes")


class VulnCandidateResult(BaseModel):
    """A potential vulnerability candidate identified during recon."""
    component: Optional[str] = Field(default=None, description="Affected component (e.g. plugin name)")
    detected_version: Optional[str] = Field(default=None, description="Version detected on target")
    cve_id: Optional[str] = Field(default=None, description="CVE ID if known")
    title: Optional[str] = Field(default=None, description="Brief vulnerability title")
    confidence: float = Field(default=0.5, description="Confidence 0.0-1.0")


class EntryPointResult(BaseModel):
    """A potential attack entry point."""
    location: str = Field(description="URL path or parameter")
    type: str = Field(description="form, api, header, cookie, file_upload, query_param, path_param")
    input_type: str = Field(default="", description="text, number, file, etc.")
    validation_observed: str = Field(default="", description="What validation was observed")
    notes: str = Field(default="", description="Additional notes")


class ReconResult(BaseModel):
    """Structured result from the recon agent — all findings in one response."""
    if ConfigDict is not None:  # pydantic v2
        model_config = ConfigDict(extra="ignore")

    summary: str = Field(
        description="Brief summary of all reconnaissance findings"
    )
    priority_targets: list[str] = Field(
        default_factory=list,
        description="High-value targets the pentester should test first"
    )
    canonical_access: Optional[CanonicalAccessResult] = Field(
        default=None,
        description="Canonical access tuple for consistent tool usage"
    )
    endpoints: list[EndpointResult] = Field(
        default_factory=list,
        description="All discovered endpoints"
    )
    technologies: list[TechnologyResult] = Field(
        default_factory=list,
        description="All detected technologies and frameworks"
    )
    components: list[ComponentResult] = Field(
        default_factory=list,
        description="Discovered components (plugins, themes, modules)"
    )
    entry_points: list[EntryPointResult] = Field(
        default_factory=list,
        description="All potential attack entry points"
    )
    auth_type: Optional[str] = Field(
        default=None,
        description="Authentication mechanism detected (jwt, session, basic, oauth, api_key, none)"
    )
    login_endpoint: Optional[str] = Field(
        default=None,
        description="Login endpoint if found"
    )
    registration_available: bool = Field(
        default=False,
        description="Whether registration is available"
    )
    key_findings: list[str] = Field(
        default_factory=list,
        description="Key findings and observations from recon"
    )
    vulnerability_candidates: list[VulnCandidateResult] = Field(
        default_factory=list,
        description="Potential vulnerability candidates based on version detection (DO NOT exploit, just identify)"
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Free-form observations (e.g. found credentials in HTML, interesting headers)"
    )

    # Extra fields sourced from ReconData state (populated after LLM response)
    ip_address: Optional[str] = Field(
        default=None,
        description="IP address of the target host"
    )
    ports_open: list[int] = Field(
        default_factory=list,
        description="List of open ports discovered"
    )
    headers_of_interest: list[str] = Field(
        default_factory=list,
        description="HTTP response headers of interest (e.g. Server, X-Powered-By)"
    )
    cookies_observed: list[str] = Field(
        default_factory=list,
        description="Cookie names observed in responses"
    )
    default_credentials_found: bool = Field(
        default=False,
        description="Whether default credentials were found"
    )
