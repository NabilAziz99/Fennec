"""
CLI Visualizer for Fennec AI.

Provides clean, structured output for:
- Tool executions (INPUT/OUTPUT)
- Hypothesis tree visualization
- Agent activity

Supports dual output:
- CLI (with ANSI colors) - for terminal display
- Logger (plain text) - for debugging and log files
"""

import json
import logging
import re
from typing import Optional
from datetime import datetime


# Create logger for visualizer
viz_logger = logging.getLogger("fennec.viz")


# =============================================================================
# Configuration
# =============================================================================

class VisualizerConfig:
    """Configuration for visualizer output."""

    # Enable CLI output (print with colors)
    cli_enabled: bool = True

    # Enable logging output (plain text to logger)
    log_enabled: bool = True

    # Log level for visualizer messages
    log_level: int = logging.INFO

    @classmethod
    def disable_cli(cls):
        """Disable CLI output (useful for tests)."""
        cls.cli_enabled = False

    @classmethod
    def enable_cli(cls):
        """Enable CLI output."""
        cls.cli_enabled = True

    @classmethod
    def disable_logging(cls):
        """Disable logging output."""
        cls.log_enabled = False

    @classmethod
    def enable_logging(cls):
        """Enable logging output."""
        cls.log_enabled = True


# =============================================================================
# ANSI Colors
# =============================================================================

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"


# Agent colors (4-role architecture)
AGENT_COLORS = {
    "orchestrator": Colors.WHITE,
    "recon": Colors.CYAN,
    "analyst": Colors.MAGENTA,
    "pentester": Colors.RED,
    "coder": Colors.GREEN,
}

# Status icons
STATUS_ICONS = {
    "pending": "○",
    "running": "●",
    "completed": "✓",
    "failed": "✗",
    "blocked": "◌",
}


# =============================================================================
# Output Helpers
# =============================================================================

def _strip_ansi(text: str) -> str:
    """Remove ANSI color codes from text for logging."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def _output(message: str, log_message: str = None):
    """
    Output to both CLI and logger based on config.

    Args:
        message: The formatted message (may contain ANSI colors)
        log_message: Optional plain text message for logger (if different from message)
    """
    if VisualizerConfig.cli_enabled:
        print(message)

    if VisualizerConfig.log_enabled:
        # Use log_message if provided, otherwise strip ANSI from message
        plain_msg = log_message if log_message else _strip_ansi(message)
        viz_logger.log(VisualizerConfig.log_level, plain_msg)


def _output_no_newline(message: str, log_message: str = None):
    """Output without newline (for progress bars)."""
    if VisualizerConfig.cli_enabled:
        print(message, end="", flush=True)

    # Don't log progress updates to avoid spam


# =============================================================================
# Utility Functions
# =============================================================================

def _truncate(text: str, max_len: int = 100) -> str:
    """Truncate text with ellipsis."""
    if not text:
        return ""
    text = str(text).replace("\n", " ").strip()
    if len(text) > max_len:
        return text[:max_len-3] + "..."
    return text


def _format_json_compact(data: dict, max_len: int = 80) -> str:
    """Format dict as compact JSON string."""
    try:
        s = json.dumps(data, separators=(',', ':'))
        return _truncate(s, max_len)
    except:
        return _truncate(str(data), max_len)


# =============================================================================
# Header Functions
# =============================================================================

def print_header(title: str, char: str = "─"):
    """Print a section header."""
    width = 60
    _output(f"\n{Colors.BOLD}{char * width}{Colors.RESET}", f"\n{'=' * width}")
    _output(f"{Colors.BOLD}  {title}{Colors.RESET}", f"  {title}")
    _output(f"{Colors.BOLD}{char * width}{Colors.RESET}", f"{'=' * width}")


def print_agent_header(agent: str):
    """Print agent header with color."""
    color = AGENT_COLORS.get(agent, Colors.WHITE)
    icon = {
        "orchestrator": "🧠",
        "recon": "🔍",
        "analyst": "💡",
        "pentester": "⚔️",
        "coder": "💻",
    }.get(agent, "▶")

    _output(
        f"\n{color}{Colors.BOLD}┌{'─' * 58}┐{Colors.RESET}",
        f"\n┌{'─' * 58}┐"
    )
    _output(
        f"{color}{Colors.BOLD}│ {icon} {agent.upper():55}│{Colors.RESET}",
        f"│ [{agent.upper()}]"
    )
    _output(
        f"{color}{Colors.BOLD}└{'─' * 58}┘{Colors.RESET}",
        f"└{'─' * 58}┘"
    )


# =============================================================================
# Tool Functions
# =============================================================================

def print_tool_call(tool_name: str, tool_input: dict, agent: str = None):
    """Print a tool call with input."""
    color = AGENT_COLORS.get(agent, Colors.WHITE) if agent else Colors.GRAY

    # Tool icon based on type
    icon = {
        "terminal": "⚡",
        "browser": "🌐",
        "file_read": "📄",
        "file_write": "✏️",
        "add_endpoint": "📍",
        "add_technology": "🔧",
        "add_entry_point": "🎯",
        "create_hypothesis": "💡",
        "create_correlation": "🔗",
        "request_recon": "🔍",
        "request_hypothesis": "💡",
        "report_result": "📊",
    }.get(tool_name, "🔧")

    _output(
        f"\n  {color}{icon} {Colors.BOLD}{tool_name}{Colors.RESET}",
        f"\n  TOOL: {tool_name}"
    )

    # Format input based on tool type
    if tool_name == "terminal":
        cmd = tool_input.get("command", "")
        _output(
            f"     {Colors.DIM}INPUT:{Colors.RESET}  {Colors.CYAN}{_truncate(cmd, 70)}{Colors.RESET}",
            f"     INPUT: {_truncate(cmd, 70)}"
        )
    elif tool_name in ["add_endpoint", "add_technology", "add_entry_point", "create_hypothesis"]:
        # Show key fields only
        key_fields = {k: v for k, v in tool_input.items() if v and k not in ["message", "notes"] and not k.startswith("_")}
        _output(
            f"     {Colors.DIM}INPUT:{Colors.RESET}  {_format_json_compact(key_fields)}",
            f"     INPUT: {_format_json_compact(key_fields)}"
        )
    else:
        # Compact JSON for others
        clean_input = {k: v for k, v in tool_input.items() if v and k != "message"}
        if clean_input:
            _output(
                f"     {Colors.DIM}INPUT:{Colors.RESET}  {_format_json_compact(clean_input)}",
                f"     INPUT: {_format_json_compact(clean_input)}"
            )


def print_tool_result(result: str, success: bool = True, agent: str = None):
    """Print tool result/output."""
    color = Colors.GREEN if success else Colors.RED
    status = "OUTPUT" if success else "ERROR"

    # Truncate and clean result
    result_str = _truncate(str(result), 200)

    _output(
        f"     {Colors.DIM}{status}:{Colors.RESET} {color}{result_str}{Colors.RESET}",
        f"     {status}: {result_str}"
    )


# =============================================================================
# Hypothesis Functions
# =============================================================================

def print_hypothesis_tree(hypotheses: list, current_id: str = None, show_all: bool = False):
    """
    Print the hypothesis tree visualization.

    Args:
        hypotheses: List of hypothesis dicts
        current_id: ID of currently active hypothesis
        show_all: If False, only show pending/running (less noise)
    """
    if not hypotheses:
        return

    _output(f"\n  {Colors.BOLD}📋 Hypothesis Queue{Colors.RESET}", "\n  HYPOTHESIS QUEUE:")

    # Group by status
    pending = []
    running = []
    completed = []

    for h in hypotheses:
        status = h.get("status", "pending")
        if status == "pending":
            pending.append(h)
        elif status == "running":
            running.append(h)
        elif status in ["completed", "failed"]:
            completed.append(h)

    # Show running first
    for h in running:
        _print_hypothesis_line(h, current_id, is_running=True)

    # Show pending
    for h in pending[:5]:  # Limit to 5
        _print_hypothesis_line(h, current_id)

    if len(pending) > 5:
        _output(
            f"     {Colors.DIM}... and {len(pending) - 5} more pending{Colors.RESET}",
            f"     ... and {len(pending) - 5} more pending"
        )

    # Completed summary (if show_all)
    if show_all and completed:
        vuln_count = sum(1 for h in completed if h.get("result") == "vulnerable")
        _output(
            f"     {Colors.DIM}Completed: {len(completed)} ({vuln_count} vulnerable){Colors.RESET}",
            f"     Completed: {len(completed)} ({vuln_count} vulnerable)"
        )


def _print_hypothesis_line(h: dict, current_id: str = None, is_running: bool = False):
    """Print a single hypothesis line."""
    hid = h.get("id", "")[:6]
    title = _truncate(h.get("title", "Untitled"), 40)
    agent = h.get("required_agent", "pentester")
    priority = h.get("priority", 0.5)

    # Status icon
    if is_running:
        icon = f"{Colors.YELLOW}●{Colors.RESET}"
        plain_icon = "[RUNNING]"
    elif hid == current_id[:6] if current_id else False:
        icon = f"{Colors.GREEN}▶{Colors.RESET}"
        plain_icon = "[CURRENT]"
    else:
        icon = f"{Colors.DIM}○{Colors.RESET}"
        plain_icon = "[PENDING]"

    # Agent color
    agent_color = AGENT_COLORS.get(agent, Colors.WHITE)
    agent_short = agent[:4] if agent else "????"

    # Priority indicator
    if priority >= 0.8:
        pri = f"{Colors.RED}!!{Colors.RESET}"
        plain_pri = "!!"
    elif priority >= 0.5:
        pri = f"{Colors.YELLOW}!{Colors.RESET} "
        plain_pri = "! "
    else:
        pri = "  "
        plain_pri = "  "

    _output(
        f"     {icon} {pri}{title} {Colors.DIM}({agent_color}{agent_short}{Colors.RESET}{Colors.DIM}){Colors.RESET}",
        f"     {plain_icon} {plain_pri}{title} ({agent_short})"
    )


def print_hypothesis_added(hypothesis: dict):
    """Print notification when hypothesis is added."""
    title = _truncate(hypothesis.get("title", ""), 50)
    agent = hypothesis.get("required_agent", "pentester")
    agent_color = AGENT_COLORS.get(agent, Colors.WHITE)

    _output(
        f"\n  {Colors.GREEN}+ NEW HYPOTHESIS:{Colors.RESET} {title}",
        f"\n  + NEW HYPOTHESIS: {title}"
    )
    _output(
        f"    {Colors.DIM}Agent: {agent_color}{agent}{Colors.RESET}",
        f"    Agent: {agent}"
    )


def print_hypothesis_completed(hypothesis: dict, result: str):
    """Print notification when hypothesis is completed."""
    title = _truncate(hypothesis.get("title", ""), 50)

    if result == "vulnerable":
        icon = f"{Colors.RED}🔓{Colors.RESET}"
        result_text = f"{Colors.RED}VULNERABLE{Colors.RESET}"
        plain_result = "VULNERABLE"
    elif result == "safe":
        icon = "✓"
        result_text = f"{Colors.GREEN}Safe{Colors.RESET}"
        plain_result = "Safe"
    else:
        icon = "○"
        result_text = f"{Colors.YELLOW}{result}{Colors.RESET}"
        plain_result = result

    _output(
        f"\n  {icon} {Colors.DIM}Completed:{Colors.RESET} {title}",
        f"\n  COMPLETED: {title}"
    )
    _output(
        f"    {Colors.DIM}Result:{Colors.RESET} {result_text}",
        f"    Result: {plain_result}"
    )


# =============================================================================
# Finding Functions
# =============================================================================

def print_finding(finding: dict):
    """Print a security finding."""
    severity = finding.get("severity", "info").upper()
    title = finding.get("title", "Finding")
    location = finding.get("location", "")

    # Severity colors
    sev_colors = {
        "CRITICAL": Colors.RED + Colors.BOLD,
        "HIGH": Colors.RED,
        "MEDIUM": Colors.YELLOW,
        "LOW": Colors.CYAN,
        "INFO": Colors.GRAY,
    }
    sev_color = sev_colors.get(severity, Colors.WHITE)

    _output(
        f"\n  {sev_color}[{severity}]{Colors.RESET} {Colors.BOLD}{title}{Colors.RESET}",
        f"\n  [{severity}] {title}"
    )
    if location:
        _output(
            f"    {Colors.DIM}Location:{Colors.RESET} {location}",
            f"    Location: {location}"
        )


def print_correlation(correlation: dict):
    """Print a correlation."""
    title = correlation.get("title", "Correlation")
    chain = correlation.get("attack_chain", "")

    _output(
        f"\n  {Colors.YELLOW}🔗 CORRELATION:{Colors.RESET} {title}",
        f"\n  CORRELATION: {title}"
    )
    if chain:
        _output(
            f"    {Colors.DIM}Chain:{Colors.RESET} {_truncate(chain, 60)}",
            f"    Chain: {_truncate(chain, 60)}"
        )


# =============================================================================
# Summary Functions
# =============================================================================

def print_recon_summary(recon_data: dict):
    """Print recon data summary."""
    endpoints = recon_data.get("endpoints", [])
    technologies = recon_data.get("technologies", [])
    entry_points = recon_data.get("entry_points", [])

    _output(
        f"\n  {Colors.CYAN}📊 Recon Summary{Colors.RESET}",
        f"\n  RECON SUMMARY:"
    )
    _output(f"     Endpoints: {len(endpoints)}")
    _output(f"     Technologies: {len(technologies)}")
    _output(f"     Entry Points: {len(entry_points)}")
    for note in recon_data.get("notes", []):
        _output(f"     Note: {note}")
    # Show technologies
    if technologies:
        tech_names = [t.get("name", "") for t in technologies[:5]]
        _output(
            f"     {Colors.DIM}Tech:{Colors.RESET} {', '.join(tech_names)}",
            f"     Tech: {', '.join(tech_names)}"
        )


# =============================================================================
# Progress & Status Functions
# =============================================================================

def print_progress(current: int, total: int, label: str = "Progress"):
    """Print a simple progress indicator."""
    pct = int((current / total) * 100) if total > 0 else 0
    bar_len = 20
    filled = int(bar_len * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_len - filled)

    _output_no_newline(
        f"\r  {Colors.DIM}{label}:{Colors.RESET} [{Colors.GREEN}{bar}{Colors.RESET}] {pct}% ({current}/{total})"
    )


def print_status(message: str, status: str = "info"):
    """Print a status message."""
    icons = {
        "info": f"{Colors.BLUE}ℹ{Colors.RESET}",
        "success": f"{Colors.GREEN}✓{Colors.RESET}",
        "warning": f"{Colors.YELLOW}⚠{Colors.RESET}",
        "error": f"{Colors.RED}✗{Colors.RESET}",
    }
    plain_icons = {
        "info": "[INFO]",
        "success": "[OK]",
        "warning": "[WARN]",
        "error": "[ERROR]",
    }
    icon = icons.get(status, icons["info"])
    plain_icon = plain_icons.get(status, "[INFO]")
    _output(f"  {icon} {message}", f"  {plain_icon} {message}")


def print_divider():
    """Print a subtle divider."""
    _output(
        f"  {Colors.DIM}{'─' * 56}{Colors.RESET}",
        f"  {'─' * 56}"
    )
