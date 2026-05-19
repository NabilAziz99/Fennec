#!/usr/bin/env python3
"""
Fennec AI Agent Interface

Clean, importable interface for running penetration tests programmatically.
Designed for integration with benchmark harnesses and automated testing.

Usage:
    from agent import run_pentest, PentestTask, AgentResult, PentestMode

    task = PentestTask(
        target_url="http://localhost:8000",
        description="Identify vulnerabilities",
        mode=PentestMode.BLACK_BOX,
        tags=["ssti"],
    )

    result = await run_pentest(task)
    print(f"Success: {result.success}")
"""

import asyncio
import logging
import re
import sys
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Awaitable, Callable, Optional, Any

# Add project to path
project_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(project_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Load .env from project directory (works even when called from other directories)
from dotenv import load_dotenv
env_path = os.path.join(project_dir, ".env")
load_dotenv(env_path, override=True)

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from src.config.settings import get_config
from src.state.graph_state import (
    SessionContext,
    ContainerInfo,
    create_initial_state,
)
from src.docker.client import DockerClient, ContainerConfig
from src.graph import compile_role_based_graph


logger = logging.getLogger("fennec.agent")


class PentestMode(str, Enum):
    """Penetration testing mode."""
    BLACK_BOX = "black_box"  # No source code access, external testing only
    WHITE_BOX = "white_box"  # Full source code access, internal analysis


@dataclass
class PentestTask:
    """Input specification for a penetration test."""
    target_url: str
    description: str
    mode: PentestMode = PentestMode.BLACK_BOX
    hint: str = ""
    tags: list[str] = field(default_factory=list)
    timeout: int = 600  # Max time in seconds
    source_code_path: Optional[str] = None  # For white box mode
    additional_context: str = ""  # Any extra context for the agent
    recon_data_path: Optional[str] = None  # Path to JSON file to skip recon

    def to_prompt(self) -> str:
        """Convert task to agent prompt."""
        prompt_parts = [
            f"Target: {self.target_url}",
            f"Objective: {self.description}",
        ]

        if self.hint:
            prompt_parts.append(f"Hint: {self.hint}")

        if self.tags:
            prompt_parts.append(f"Vulnerability tags: {', '.join(self.tags)}")

        if self.mode == PentestMode.WHITE_BOX and self.source_code_path:
            prompt_parts.append(f"Source code available at: {self.source_code_path}")
            prompt_parts.append("Mode: WHITE BOX - You have access to source code for analysis")
        else:
            prompt_parts.append("Mode: BLACK BOX - External testing only, no source code access")

        if self.additional_context:
            prompt_parts.append(f"Additional context: {self.additional_context}")

        prompt_parts.append("")
        prompt_parts.append("Identify and exploit vulnerabilities in the target.")

        return "\n".join(prompt_parts)


@dataclass
class AgentResult:
    """Result from a penetration test run."""
    success: bool
    vulnerabilities: list[str] = field(default_factory=list)
    exploits_used: list[str] = field(default_factory=list)
    execution_log: list[dict] = field(default_factory=list)
    error: Optional[str] = None
    duration_seconds: float = 0.0
    token_usage: dict = field(default_factory=dict)
    final_summary: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "vulnerabilities": self.vulnerabilities,
            "exploits_used": self.exploits_used,
            "execution_log": self.execution_log,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
            "token_usage": self.token_usage,
            "final_summary": self.final_summary,
        }


def _running_inside_container() -> bool:
    """Heuristic check: are we executing inside a Docker container?

    `/.dockerenv` is created by Docker for every container. The cgroup file
    contains "docker" or "containerd" inside containers run by typical
    container runtimes. Either signal is sufficient.
    """
    if os.path.exists("/.dockerenv"):
        return True
    try:
        with open("/proc/1/cgroup", "r") as fh:
            data = fh.read()
        return "docker" in data or "containerd" in data or "kubepods" in data
    except OSError:
        return False


def convert_localhost_for_docker(url: str) -> str:
    """Convert localhost URLs to host.docker.internal for Docker containers.

    Fires on:
    - macOS / Windows hosts (Docker Desktop handles host.docker.internal)
    - Linux when the agent itself is running inside a container (e.g.
      `docker compose up`) — needs the `host.docker.internal:host-gateway`
      extra_hosts entry on the agent's compose service to resolve.

    On a bare Linux host running the agent directly, `localhost` already
    works from the spawned Kali sibling container via the default bridge,
    so we leave the URL unchanged there.
    """
    import platform

    needs_rewrite = (
        platform.system() in ("Darwin", "Windows")
        or _running_inside_container()
    )
    if needs_rewrite:
        url = re.sub(r'(https?://)localhost(:\d+)?', r'\1host.docker.internal\2', url)
        url = re.sub(r'(https?://)127\.0\.0\.1(:\d+)?', r'\1host.docker.internal\2', url)

    return url


def _resolve_execution_mode() -> str:
    """Resolve execution mode from environment variables."""
    mode = os.getenv("EXECUTION_MODE", "").strip().lower()
    if mode:
        return mode
    use_docker = os.getenv("USE_DOCKER", "").strip().lower()
    if use_docker in ("0", "false", "no", "off"):
        return "local"
    return "docker"


async def _get_review_decision(interrupt_data: dict) -> dict:
    """Prompt the operator for HTLI review decision via stdin."""
    hypotheses = interrupt_data.get("hypotheses", [])
    pending = [h for h in hypotheses if h.get("status") == "pending"]

    print("\n" + "=" * 60)
    print("  HUMAN REVIEW REQUIRED (HTLI mode)")
    print("=" * 60)
    if pending:
        print(f"  Analyst produced {len(pending)} pending hypothesis/es:\n")
        for i, h in enumerate(pending, 1):
            print(f"  {i}. {h.get('title', '?')}")
            desc = h.get("description", "")
            if desc:
                print(f"     {desc}")
    else:
        print("  No pending hypotheses.")

    print("\n  [Enter/y] Approve   [q] Abort")
    try:
        answer = input("  Your choice: ").strip().lower()
    except EOFError:
        answer = "y"

    if answer in ("q", "quit", "abort"):
        return {"abort": True}
    return {}


async def run_pentest(
    task: PentestTask,
    verbose: bool = False,
    graph_name: str = "main",
    htli: bool = False,
    event_sink: Optional[Callable[[str, dict], Awaitable[None]]] = None,
    await_review: Optional[Callable[[dict], Awaitable[dict]]] = None,
) -> AgentResult:
    """
    Run Fennec AI agent against a target.

    Args:
        task: PentestTask specification
        verbose: Whether to print progress to stdout
        graph_name: Role-based graph name to compile (default: "main")
        htli: Human-In-The-Loop mode — pause for confirmation before tool calls
        event_sink: Optional async callback that receives (event_type, data)
            tuples as the agent loop progresses. The API server uses this to
            publish SSE events to dashboard subscribers.
        await_review: Optional async callback invoked when the graph emits an
            HTLI interrupt. It receives the interrupt payload and must return
            the operator's user_edits dict. Falls back to stdin prompt when
            not provided (the CLI path).

    Returns:
        AgentResult with findings
    """
    async def _emit(event_type: str, data: dict) -> None:
        """Safe event publish — never lets a bad sink kill the agent."""
        if event_sink is None:
            return
        try:
            await event_sink(event_type, data)
        except Exception as exc:  # pragma: no cover — defensive
            logger.debug("event_sink raised on %s: %s", event_type, exc)
    # Resolve htli from env if not explicitly set
    if not htli:
        htli = os.getenv("HTLI", "").strip().lower() in ("1", "true", "yes", "on")

    start_time = time.time()
    session_id = str(uuid.uuid4())

    logger.info(f"Starting pentest session {session_id}")
    if htli:
        logger.info("Human-In-The-Loop (HTLI) mode enabled")

    logger.info(f"Target: {task.target_url}")
    logger.info(f"Mode: {task.mode.value}")

    # Convert localhost for Docker access
    execution_mode = _resolve_execution_mode()
    docker_target_url = task.target_url
    if execution_mode == "docker":
        docker_target_url = convert_localhost_for_docker(task.target_url)
        if docker_target_url != task.target_url:
            logger.info(f"Docker target: {docker_target_url}")
    else:
        logger.info("Execution mode: local (Docker disabled)")

    # Initialize result
    result = AgentResult(success=False)
    execution_log: list[dict] = []
    # Initialize here (not deeper) so the post-run finalization can read it
    # even if setup fails before the streaming loop starts (e.g. Docker not
    # running). Without this, an early-setup exception leaves the variable
    # unbound and the post-run finalization raises UnboundLocalError.
    _latest_hypothesis_manager: Optional[dict] = None

    # Get config
    config = get_config()

    docker_client = DockerClient() if execution_mode == "docker" else None

    try:
        if docker_client:
            await docker_client.initialize()
            logger.info("Docker client initialized")

        # Initialize LLMs (default + per-agent overrides)
        from src.config.settings import create_llm

        llm = create_llm(config.llm_model)

        # Create per-agent LLM overrides if configured
        llm_recon = create_llm(config.recon_llm_model) if config.recon_llm_model else None
        llm_analyst = create_llm(config.analyst_llm_model) if config.analyst_llm_model else None
        llm_pentester = create_llm(config.pentester_llm_model) if config.pentester_llm_model else None

        logger.info(f"LLM initialized: {config.llm_provider}/{config.llm_model}")
        if config.recon_llm_model:
            logger.info(f"  Recon LLM: {config.recon_llm_model}")
        if config.analyst_llm_model:
            logger.info(f"  Analyst LLM: {config.analyst_llm_model}")
        if config.pentester_llm_model:
            logger.info(f"  Pentester LLM: {config.pentester_llm_model}")

        container_id = None
        try:
            # Spawn the Kali sibling container. We do this *inside* the
            # try/finally that owns cleanup, so cancellation between spawn
            # and the graph loop can never leak a container.
            if docker_client:
                # Pre-flight: verify the image exists locally before we try to
                # spawn. Otherwise aiodocker emits a generic 404 buried in a
                # JSON blob and users don't realise they forgot to build it.
                try:
                    await docker_client._client.images.inspect(config.docker_image)
                except Exception:
                    raise RuntimeError(
                        f"Docker image '{config.docker_image}' not found locally. "
                        f"Build it first:\n"
                        f"    cd linux && make build\n"
                        f"Or override with DOCKER_IMAGE=<some-image> in .env "
                        f"(e.g. DOCKER_IMAGE=kalilinux/kali-rolling:latest)."
                    )
                container_config = ContainerConfig(
                    image=config.docker_image,
                    name=f"fennec-bench-{session_id[:8]}",
                )
                container_id = await docker_client.spawn_container(container_config)
                logger.info(f"Container created: {container_id[:12]}")

            # Create session context
            container_info = None
            if container_id:
                container_info = ContainerInfo(
                    container_id=container_id,
                    image=config.docker_image,
                )
            session = SessionContext(
                session_id=session_id,
                flow_id=str(uuid.uuid4()),
                container=container_info,
                docker_image=config.docker_image,
                language="en",
            )

            # Build prompt based on task
            prompt = task.to_prompt()

            # Load pre-built recon data if provided (skip recon phase)
            initial_recon_data = None
            if task.recon_data_path:
                import json as _json
                with open(task.recon_data_path, "r") as f:
                    initial_recon_data = _json.load(f)
                logger.info(f"Loaded recon data from {task.recon_data_path} — skipping recon phase")

            # Load assessment method from environment
            method = os.getenv("FENNEC_METHOD", "balanced")
            from src.config.settings import get_method_preset
            method_preset = get_method_preset(method)
            logger.info(f"Assessment method: {method} (timeout={method_preset['task_timeout']}s, recursion={method_preset['recursion_limit']})")

            # Load auth credentials from FENNEC_AUTH_CREDENTIALS env (JSON blob).
            # Set this when the target requires login; agents will use it to
            # authenticate to the target during recon and pentest.
            auth_credentials = None
            auth_creds_env = os.getenv("FENNEC_AUTH_CREDENTIALS")
            if auth_creds_env:
                import json as _creds_json
                try:
                    auth_credentials = _creds_json.loads(auth_creds_env)
                    logger.info(f"Auth credentials loaded from env for user: {auth_credentials.get('username', 'unknown')}")
                except Exception:
                    logger.warning("Failed to parse FENNEC_AUTH_CREDENTIALS")

            # Create initial state
            initial_state = create_initial_state(
                session=session,
                target_url=docker_target_url,
                has_source_code=task.mode == PentestMode.WHITE_BOX,
                has_live_target=True,
                task_description=task.description,
                task_hint=task.hint,
                initial_recon_data=initial_recon_data,
                auth_credentials=auth_credentials,
                method=method,
            )
            # Override default message with task-specific prompt
            initial_state["messages"] = [HumanMessage(content=prompt)]

            # Configure runnable
            working_dir = os.getenv("WORKING_DIR", "/work")
            if execution_mode == "local":
                Path(working_dir).mkdir(parents=True, exist_ok=True)
            configurable_dict = {
                    "llm": llm,
                    "llm_recon": llm_recon,
                    "llm_analyst": llm_analyst,
                    "llm_pentester": llm_pentester,
                    "docker_client": docker_client,
                    "container_id": container_id,
                    "working_dir": working_dir,
                    "execution_mode": execution_mode,
                    "htli": htli,
                    "tavily_api_key": config.tavily_api_key,
                    "perplexity_api_key": config.perplexity_api_key,
                    "method_preset": method_preset,
            }
            if htli:
                configurable_dict["thread_id"] = f"session-{session_id}"
            runnable_config = RunnableConfig(
                configurable=configurable_dict,
                recursion_limit=method_preset["recursion_limit"],
            )

            # Compile and run graph
            graph = compile_role_based_graph(graph_name=graph_name, htli=htli)
            logger.info("Starting agent execution...")

            current_agent = "orchestrator"
            all_content = []
            evidence_outputs: list[str] = []
            pending_tool_calls = {}  # Track tool calls waiting for results
            # _latest_hypothesis_manager is initialised at function scope so
            # the post-run finalization can read it even when setup fails
            # before this point. The inner-loop assignment below updates it
            # as the hypothesis_manager state changes during streaming.

            graph_input: Any = initial_state  # first run uses initial_state

            while True:
                interrupted = False
                timed_out = False

                async for event in graph.astream(graph_input, runnable_config):
                    # Check timeout
                    elapsed = time.time() - start_time
                    effective_timeout = method_preset.get("task_timeout", task.timeout)
                    if elapsed > effective_timeout:
                        logger.warning(f"Timeout reached ({effective_timeout}s, method={method})")
                        timed_out = True
                        break

                    for node_name, node_output in event.items():
                        if node_name == "__interrupt__":
                            # Extract interrupt payload
                            interrupt_value = node_output
                            if isinstance(node_output, (list, tuple)) and len(node_output) > 0:
                                first = node_output[0]
                                interrupt_value = first.value if hasattr(first, 'value') else first
                            interrupt_data = interrupt_value if isinstance(interrupt_value, dict) else {}

                            # Surface the interrupt to subscribers (dashboard
                            # uses this to flip its UI into "awaiting review").
                            await _emit("hypothesis_review", interrupt_data)

                            # Prefer the API hook when present, fall back to
                            # the CLI stdin prompt for direct `python cli.py`
                            # invocations.
                            if await_review is not None:
                                user_edits = await await_review(interrupt_data)
                            else:
                                user_edits = await _get_review_decision(interrupt_data)

                            graph_input = Command(resume=user_edits)
                            interrupted = True
                            break  # break inner for loop

                        if node_output is None:
                            continue
                        # Track agent transitions
                        prev_agent = current_agent
                        if isinstance(node_output, dict) and node_output.get("next_agent"):
                            next_agent = node_output["next_agent"]
                            current_agent = next_agent.value if hasattr(next_agent, 'value') else str(next_agent)
                        if node_name and (prev_agent != current_agent or node_name != prev_agent):
                            await _emit("node_update", {"node": node_name, "agent": current_agent})

                        # Stream rich state changes for the dashboard. We emit
                        # the whole serialized blob on each update — these are
                        # snapshots, not deltas, so dropped events recover on
                        # the next one.
                        if isinstance(node_output, dict):
                            if node_output.get("recon_data") is not None:
                                await _emit("recon_update", {"recon_data": node_output["recon_data"]})
                            if node_output.get("hypothesis_manager") is not None:
                                await _emit("hypothesis_tree", {"hypothesis_manager": node_output["hypothesis_manager"]})
                            if node_output.get("current_hypothesis_id"):
                                await _emit("current_hypothesis", {"hypothesis_id": node_output["current_hypothesis_id"]})
                            if node_output.get("correlation_store") is not None:
                                await _emit("findings_update", {"correlation_store": node_output["correlation_store"]})
                            if node_output.get("final_result"):
                                await _emit("result", {"final_result": str(node_output["final_result"])})
                            if node_output.get("pending_agent_result"):
                                await _emit("agent_result", node_output["pending_agent_result"])

                        # Process messages
                        if not isinstance(node_output, dict):
                            continue
                        messages = node_output.get("messages", [])
                        for msg in messages:
                            msg_type = type(msg).__name__
                            timestamp = datetime.now().isoformat()

                            # Handle AI messages (agent reasoning + tool calls)
                            if msg_type == "AIMessage":
                                # Log agent reasoning/content
                                if hasattr(msg, "content") and msg.content:
                                    content = str(msg.content)
                                    all_content.append(content)

                                    # Log full agent message (not truncated)
                                    execution_log.append({
                                        "timestamp": timestamp,
                                        "node": node_name,
                                        "agent": current_agent,
                                        "type": "agent_message",
                                        "message": content,  # Full content
                                    })
                                    await _emit("message", {
                                        "type": "AIMessage",
                                        "agent": current_agent,
                                        "content": content,
                                        "timestamp": timestamp,
                                    })

                                    if verbose:
                                        print(f"[{current_agent.upper()}] {content[:200]}...")

                                # Log tool calls with full arguments
                                if hasattr(msg, "tool_calls") and msg.tool_calls:
                                    for tc in msg.tool_calls:
                                        tool_name = tc.get("name", "unknown")
                                        tool_args = tc.get("args", {})
                                        tool_id = tc.get("id", "")

                                        # Store pending tool call for result matching
                                        pending_tool_calls[tool_id] = {
                                            "name": tool_name,
                                            "args": tool_args,
                                            "agent": current_agent,
                                        }

                                        # Log tool call with full arguments
                                        execution_log.append({
                                            "timestamp": timestamp,
                                            "node": node_name,
                                            "agent": current_agent,
                                            "type": "tool_call",
                                            "tool_name": tool_name,
                                            "tool_id": tool_id,
                                            "args": tool_args,
                                        })
                                        await _emit("tool_call", {
                                            "tool_name": tool_name,
                                            "tool_id": tool_id,
                                            "args": tool_args,
                                            "agent": current_agent,
                                            "timestamp": timestamp,
                                        })

                                        # Track exploits used
                                        exploit_tools = ["terminal", "sqlmap", "nmap", "gobuster"]
                                        if any(t in tool_name.lower() for t in exploit_tools):
                                            if tool_name not in result.exploits_used:
                                                result.exploits_used.append(tool_name)

                                        if verbose:
                                            args_str = str(tool_args)[:100]
                                            print(f"[{current_agent.upper()}] TOOL: {tool_name}({args_str}...)")

                            # Handle Tool messages (tool results)
                            elif msg_type == "ToolMessage":
                                tool_id = getattr(msg, "tool_call_id", "")
                                tool_content = str(msg.content) if hasattr(msg, "content") else ""
                                all_content.append(tool_content)

                                # Get the original tool call info
                                tool_info = pending_tool_calls.get(tool_id, {})
                                tool_name = tool_info.get("name", getattr(msg, "name", "unknown"))
                                tool_name_normalized = str(tool_name).lower()

                                # Collect evidence from evidence-producing tools
                                evidence_tools = {"terminal", "browser", "file_read"}
                                if tool_name_normalized in evidence_tools:
                                    evidence_outputs.append(tool_content)

                                # Log tool result with full output
                                tool_status = getattr(msg, "status", "success")
                                execution_log.append({
                                    "timestamp": timestamp,
                                    "node": node_name,
                                    "agent": tool_info.get("agent", current_agent),
                                    "type": "tool_result",
                                    "tool_name": tool_name,
                                    "tool_id": tool_id,
                                    "output": tool_content,  # Full output
                                    "status": tool_status,
                                })
                                await _emit("tool_execution", {
                                    "tool_name": tool_name,
                                    "tool_id": tool_id,
                                    "agent": tool_info.get("agent", current_agent),
                                    "result": tool_content,
                                    "success": tool_status == "success",
                                    "timestamp": timestamp,
                                })

                                if verbose:
                                    print(f"[TOOL RESULT] {tool_name}: {tool_content[:200]}...")

                            # Handle Human messages
                            elif msg_type == "HumanMessage":
                                if hasattr(msg, "content") and msg.content:
                                    content = str(msg.content)
                                    execution_log.append({
                                        "timestamp": timestamp,
                                        "node": node_name,
                                        "agent": "user",
                                        "type": "human_message",
                                        "message": content,
                                    })

                        # Capture final result
                        if isinstance(node_output, dict) and node_output.get("final_result"):
                            result.final_summary = str(node_output.get("final_result", ""))

                        # Track the latest hypothesis_manager snapshot so we
                        # can read confirmed-vulnerable hypotheses off the
                        # end state into AgentResult.vulnerabilities / success.
                        if isinstance(node_output, dict) and node_output.get("hypothesis_manager"):
                            _latest_hypothesis_manager = node_output.get("hypothesis_manager")

                    if interrupted:
                        break  # break astream loop to resume with Command

                if not interrupted or timed_out:
                    break  # graph finished normally or timed out

        finally:
            if docker_client and container_id:
                await docker_client.delete_container(container_id, force=True)
                logger.info(f"Container cleaned up: {container_id[:12]}")

    except Exception as e:
        logger.error(f"Error during pentest: {e}", exc_info=True)
        result.error = str(e)

    finally:
        if docker_client:
            await docker_client.close()

    # Finalize result
    result.duration_seconds = time.time() - start_time
    result.execution_log = execution_log

    # Populate success + vulnerabilities from the hypothesis tree's terminal
    # state. Previously both fields were declared and then never written to,
    # so even runs that confirmed a vulnerability reported Success=False and
    # an empty Vulnerabilities list (dead fields left over from the old CTF
    # flag-capture era). The source of truth is the hypothesis_manager dict
    # that every agent node mutates — at end of run, any hypothesis whose
    # result == "vulnerable" is a real finding.
    if _latest_hypothesis_manager:
        tree = _latest_hypothesis_manager.get("tree") or {}
        vuln_titles: list[str] = []
        for hid, hyp in tree.items():
            if not isinstance(hyp, dict):
                continue
            if (hyp.get("result") or "").lower() == "vulnerable":
                title = hyp.get("title") or f"Finding {hid}"
                vuln_titles.append(title)
        result.vulnerabilities = vuln_titles
        if vuln_titles:
            result.success = True

    logger.info(f"Pentest completed in {result.duration_seconds:.1f}s")
    logger.info(
        f"Success: {result.success}, Vulnerabilities: {len(result.vulnerabilities)}"
    )

    return result


async def run_pentest_simple(
    target_url: str,
    description: str,
    mode: str = "black_box",
    hint: str = "",
    tags: list[str] = None,
    timeout: int = 600,
    graph_name: str = "main",
    htli: bool = False,
) -> AgentResult:
    """
    Simplified interface for running a pentest.

    Args:
        target_url: URL to test
        description: Task description
        mode: "black_box" or "white_box"
        hint: Optional hint
        tags: Vulnerability tags
        timeout: Max time in seconds
        graph_name: Role-based graph name to compile (default: "main")
        htli: Human-In-The-Loop mode

    Returns:
        AgentResult
    """
    task = PentestTask(
        target_url=target_url,
        description=description,
        mode=PentestMode(mode),
        hint=hint,
        tags=tags or [],
        timeout=timeout,
    )

    return await run_pentest(task, graph_name=graph_name, htli=htli)


# CLI interface for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fennec AI Agent")
    parser.add_argument("--target", "-t", default=None, help="Target URL (fallback: TARGET_URL env)")
    parser.add_argument("--description", "-d", default=None, help="Task description (fallback: TASK_DESCRIPTION env)")
    parser.add_argument("--mode", "-m", choices=["black_box", "white_box"], default=None, help="Test mode (fallback: MODE env)")
    parser.add_argument("--hint", default="", help="Optional hint")
    parser.add_argument("--tags", nargs="*", default=[], help="Vulnerability tags")
    parser.add_argument("--timeout", type=int, default=None, help="Timeout in seconds (fallback: TIMEOUT env)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--htli", action="store_true", default=None, help="Human-In-The-Loop: pause for review (fallback: HTLI env)")
    parser.add_argument("--graph", default="main", help="Graph name to use (default: main)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    httpx_level = os.getenv("HTTPX_LOG_LEVEL", "WARNING").upper()
    logging.getLogger("httpx").setLevel(httpx_level)

    # Resolve all args from CLI flags → env vars → defaults
    target_url = args.target or os.getenv("TARGET_URL")
    if not target_url:
        parser.error("--target or TARGET_URL env var is required")
    description = args.description or os.getenv("TASK_DESCRIPTION", "Identify and exploit vulnerabilities in the target")
    mode = args.mode or os.getenv("MODE", "black_box")
    timeout = args.timeout or int(os.getenv("TIMEOUT", "600"))

    result = asyncio.run(run_pentest_simple(
        target_url=target_url,
        description=description,
        mode=mode,
        hint=args.hint,
        tags=args.tags,
        timeout=timeout,
        graph_name=args.graph,
        htli=args.htli or False,
    ))

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    print(f"Success: {result.success}")
    print(f"Duration: {result.duration_seconds:.1f}s")
    print(f"Vulnerabilities: {result.vulnerabilities}")
    print(f"Exploits used: {result.exploits_used}")
    if result.error:
        print(f"Error: {result.error}")
