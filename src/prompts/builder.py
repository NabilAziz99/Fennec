"""
Dynamic prompt builder.

Composes agent prompts from modular sections based on context:
- Agent type (recon, analyst, pentester, coder)
- Testing mode (black-box, white-box, combined)
- Hypothesis skills (sql_injection, xss, etc.)
- Current task context
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone

from .sections import (
    AUTHORIZATION,
    PERSISTENCE,
    METHODOLOGY,
    VULNERABILITY_FOCUS,
    TODO_LIST,
    ENVIRONMENT,
    get_agent_identity,
    get_testing_mode_prompt,
    get_agent_rules,
)
from ..skills import get_skills_for_hypothesis

if TYPE_CHECKING:
    from ..state.hypothesis import Hypothesis
    from ..state.graph_state import SessionContext
    from ..state.recon import ReconData

line_break = "--------------------------------------------------------------------------------"
class PromptBuilder:
    """
    Builds agent prompts dynamically based on context.

    The prompt is composed of:
    1. Agent identity (role-specific)
    2. Authorization (always)
    3. Current hypothesis/task
    4. Testing mode (conditional)
    5. Methodology (for testing agents)
    6. Vulnerability focus (for testing agents)
    7. Environment (for terminal-using agents)
    8. Skills (dynamic, based on hypothesis)
    9. Reporting instructions
    """

    def __init__(
        self,
        agent_type: str,
        hypothesis: Optional["Hypothesis"] = None,
        target_url: str = "",
        has_source_code: bool = False,
        has_live_target: bool = True,
        session: Optional["SessionContext"] = None,
        task_description: str | None = None,
        task_hint: str | None = None,
        recon_data: Optional["ReconData"] = None,
    ):
        self.agent_type = agent_type
        self.hypothesis = hypothesis
        self.target_url = target_url
        self.has_source_code = has_source_code
        self.has_live_target = has_live_target
        self.session = session
        self.task_description = task_description
        self.task_hint = task_hint
        self.recon_data = recon_data

    def build(self) -> str:
        """Build the complete prompt."""
        sections = []
        sections.append(f"""{line_break}\nSYSTEM PROMPT\n{line_break}\n""")
        # 1. Agent identity
        sections.append(get_agent_identity(self.agent_type))

        # 2. Authorization (always)
        sections.append(AUTHORIZATION)

        if self.agent_type in ["recon", "pentester"]:
            sections.append(TODO_LIST)

        # 3. Recon data (for pentester)
        if self.agent_type == "pentester" and self.recon_data:
            sections.append(self._build_recon_section())

        # 4. Current hypothesis/task
        sections.append(self._build_hypothesis_section())

        # 4. Testing mode (for testing agents)
        if self.agent_type in ["pentester", "coder"]:
            sections.append(get_testing_mode_prompt(self.has_source_code, self.has_live_target))

        # 5. Persistence mindset (for testing agents)
        if self.agent_type in ["pentester"]:
            sections.append(PERSISTENCE)

        # 6. Methodology (for testing agents)
        if self.agent_type in ["pentester"]:
            sections.append(METHODOLOGY)

        # 7. Vulnerability focus (for testing agents)
        if self.agent_type in ["pentester"] and self.hypothesis:
            sections.append(VULNERABILITY_FOCUS)

        # 8. Environment (for agents that use terminal)
        if self.agent_type in ["pentester", "coder", "recon"]:
            sections.append(ENVIRONMENT)

        if get_agent_rules(self.agent_type):
            sections.append(get_agent_rules(self.agent_type))

        # 9. Skills (dynamic)
        if self.hypothesis and self.hypothesis.skills:
            skills_content = get_skills_for_hypothesis(self.hypothesis)
            if skills_content:
                sections.append(skills_content)

        # 10. Reporting instructions
        if self.agent_type in ["pentester"]:
            sections.append(self._build_reporting_section())

        # 11. Task context
        task_context = self._build_task_context_section()
        if task_context:
            sections.append(task_context)

        # 12. Context
        sections.append(self._build_context_section())

        return "\n\n".join(sections)

    def _build_recon_section(self) -> str:
        """Build the recon data section for pentester."""
        if not self.recon_data:
            return ""

        return f"""<recon_data>
{self.recon_data.get_summary()}
</recon_data>"""

    def _build_hypothesis_section(self) -> str:
        """Build the hypothesis/task section."""
        if not self.hypothesis:
            return f"""<current_task>
Target: {self.target_url}
No specific hypothesis assigned. Perform initial reconnaissance.
</current_task>"""

        return f"""<current_hypothesis>
HYPOTHESIS ID: {self.hypothesis.id}
TITLE: {self.hypothesis.title}
DESCRIPTION: {self.hypothesis.description}
PRIORITY: {self.hypothesis.priority}

Your job is to thoroughly test this hypothesis using multiple approaches.
Try different techniques internally before concluding.
</current_hypothesis>"""

    def _build_reporting_section(self) -> str:
        """Build the reporting instructions section."""
        return """<reporting>
WHEN YOU ARE DONE, emit a `PentesterResult` structured response.

REQUIRED top-level fields:
- status: "completed" | "needs_info" | "dead_end"
  - completed: You fully tested the hypothesis (vulnerable OR safe).
  - needs_info: Blocked, requires artifacts from another hypothesis.
  - dead_end: No viable attack path. Use the `error` field to explain why.

- verdict: only if status="completed". One of:
  "critical" | "high" | "medium" | "low" | "info"  → confirmed vulnerability
  "safe"                                            → tested, no vuln found
  "inconclusive"                                    → could not determine

- evidence: list[str]   short human-readable findings, e.g.
  ["Time-based SQLi confirmed on /login (5s delay)", "Read /etc/passwd via traversal"]

- suggested_followups: list[str]  hints for the analyst about NEW attack paths.
- needs: list[str]                only when status="needs_info".
- error: str                      only when status="dead_end".

═══════════════════════════════════════════════════════════════════════════════
RICH FINDING FIELDS (REQUIRED when verdict ∈ {critical, high, medium, low, info})
═══════════════════════════════════════════════════════════════════════════════
Skip these for verdict="safe" or "inconclusive". Otherwise fill ALL of them —
this is what gets shown to the user. Be specific, cite real evidence.

- description: {
    overview: str                # 2-4 sentence plain-English summary of the vuln
    breakdown: {                 # dict — fill these 4 keys exactly
      vuln_type: "Vertical Privilege Escalation" | "RCE" | "SQLi" | "SSRF" | etc.,
      affected_endpoint: "GET /api/user/me",
      access_required: "Standard authenticated user" | "Unauthenticated" | etc.,
      exploitability: "High - single API call" | "Medium - requires X" | etc.,
    },
    technical_details: str       # markdown, deep technical explanation of WHY it works
  }

- impact: {
    demonstrated_impact: str     # what data/access you ACTUALLY obtained
    attack_scenarios: str        # numbered real-world scenarios (1. ..., 2. ...)
    business_risk: str           # data breach? financial? compliance? specific
  }

- evidence_details: {
    logged_evidence: [           # list of HTTP request/response pairs
      {request: "GET /etc/passwd HTTP/1.1\\nHost: ...", response: "HTTP/1.1 200 OK\\n..."},
      ...
    ],
    payloads_used: ["/cgi-bin/.%2e/...", "{\\"admin\\": true}"],
    observed_behavior: str       # 1-2 sentences on how the app responded
  }

- remediation: {
    primary_mitigation: str      # markdown, the main recommended fix
    implementation_pattern: str  # short code example showing the fix
    additional_hardening: str    # markdown, extra defense-in-depth
  }

- owasp_category: e.g. "Broken Access Control", "Injection", "SSRF"

═══════════════════════════════════════════════════════════════════════════════
RULES
═══════════════════════════════════════════════════════════════════════════════
- Try multiple payload variants INTERNALLY before giving up.
- Only emit `new_hypotheses` when a DIFFERENT attack surface or agent is needed.
- Be thorough — exhaust your options before reporting dead_end.
- For confirmed vulns: capture the EXACT request/response that proved it.
  Without logged_evidence you have no proof — the finding will be downranked.
</reporting>"""

    def _build_context_section(self) -> str:
        """Build the context section."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        context = f"""<context>
{line_break}\nCONTEXT\n{line_break}
TIME: {now}
TARGET: {self.target_url}"""

        if self.session:
            context += f"""
DOCKER IMAGE: {self.session.docker_image}
WORKING DIRECTORY: {self.session.container.working_dir if self.session.container else "/work"}"""

        context += "\n</context>"
        return context

    def _build_task_context_section(self) -> str:
        """Build the task context section."""
        if not self.task_description and not self.task_hint:
            return ""

        lines = ["<task_context>"]
        lines.append(f"{line_break}\nTASK CONTEXT\n{line_break}\n")
        if self.task_description:
            lines.append(f"Objective: {self.task_description}")
        if self.task_hint:
            lines.append(f"Hint: {self.task_hint}")
        lines.append("</task_context>")
        return "\n".join(lines)


def build_prompt(
    agent_type: str,
    hypothesis: Optional["Hypothesis"] = None,
    target_url: str = "",
    has_source_code: bool = False,
    has_live_target: bool = True,
    session: Optional["SessionContext"] = None,
    task_description: str | None = None,
    task_hint: str | None = None,
    recon_data: Optional["ReconData"] = None,
) -> str:
    """
    Convenience function to build a prompt.

    Args:
        agent_type: Type of agent (recon, analyst, pentester, coder)
        hypothesis: Current hypothesis to test
        target_url: Target URL for the pentest
        has_source_code: Whether source code is available
        has_live_target: Whether a live target is available
        session: Session context
        recon_data: Reconnaissance data (endpoints, technologies, etc.)

    Returns:
        Complete prompt string
    """
    builder = PromptBuilder(
        agent_type=agent_type,
        hypothesis=hypothesis,
        target_url=target_url,
        has_source_code=has_source_code,
        has_live_target=has_live_target,
        session=session,
        task_description=task_description,
        task_hint=task_hint,
        recon_data=recon_data,
    )
    return builder.build()
