"""
Core execution tools for Docker container operations.
"""

from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
import shlex
import asyncio
import os
from pathlib import Path

try:
    from ..schemas import TerminalInput, FileReadInput, FileWriteInput, BrowserInput, WebSearchInput
except ImportError:
    from src.schemas import TerminalInput, FileReadInput, FileWriteInput, BrowserInput, WebSearchInput


def create_terminal_tool():
    """Create terminal execution tool."""

    @tool(args_schema=TerminalInput)
    async def terminal(
        command: str,
        working_dir: str = "/work",
        timeout: int = 300,
        message: str = "",
        *,
        config: RunnableConfig,
    ) -> str:
        """
        Execute a shell command in the Docker container.

        Use for running security tools like nmap, sqlmap, gobuster, etc.
        """
        configurable = config.get("configurable", {})
        docker_client = configurable.get("docker_client")
        container_id = configurable.get("container_id")
        execution_mode = configurable.get("execution_mode") or os.getenv("EXECUTION_MODE", "docker")
        working_dir = configurable.get("working_dir", "/work")

        if not docker_client or not container_id:
            if execution_mode != "local":
                return "Error: Docker not configured. Ensure docker_client and container_id are in config."

            cmd_short = command[:80] + ("..." if len(command) > 80 else "")
            print(f"  ⚡ $ {cmd_short}", flush=True)

            try:
                effective_timeout = min(int(timeout or 300), 600)
                proc = await asyncio.create_subprocess_shell(
                    command,
                    cwd=working_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    executable="/bin/bash",
                )
                try:
                    output, _ = await asyncio.wait_for(proc.communicate(), timeout=effective_timeout)
                except asyncio.TimeoutError:
                    proc.kill()
                    return "Command timed out"
                text = output.decode("utf-8", errors="replace") if output else ""
                return text[:10000] if len(text) > 10000 else text
            except Exception as e:
                return f"Error executing command: {e}"

        # Real-time visibility: print command as it runs
        cmd_short = command[:80] + ("..." if len(command) > 80 else "")
        print(f"  ⚡ $ {cmd_short}", flush=True)

        try:
            # Enforce a hard timeout inside the container as well. This protects against
            # cases where the Docker exec stream blocks and asyncio cancellation isn't enough.
            effective_timeout = min(int(timeout or 300), 600)
            quoted = shlex.quote(command)
            wrapped_command = (
                f'if command -v timeout >/dev/null 2>&1; then '
                f'timeout -k 5 {effective_timeout}s bash -lc {quoted}; '
                f'else bash -lc {quoted}; fi'
            )
            result = await docker_client.exec_command(
                container_id=container_id,
                command=wrapped_command,
                cwd=working_dir,
                # Give the outer wait_for a small grace window to allow `timeout` to terminate the process.
                timeout=min(effective_timeout + 20, 620),
            )
            output = result.output if hasattr(result, 'output') else str(result)
            return output[:10000] if len(output) > 10000 else output
        except Exception as e:
            return f"Error executing command: {e}"

    return terminal


def create_file_read_tool():
    """Create file read tool."""

    @tool(args_schema=FileReadInput)
    async def file_read(
        path: str,
        message: str = "",
        *,
        config: RunnableConfig,
    ) -> str:
        """Read a file from the Docker container."""
        configurable = config.get("configurable", {})
        docker_client = configurable.get("docker_client")
        container_id = configurable.get("container_id")
        execution_mode = configurable.get("execution_mode") or os.getenv("EXECUTION_MODE", "docker")
        working_dir = configurable.get("working_dir", "/work")

        if not docker_client or not container_id:
            if execution_mode != "local":
                return "Error: Docker not configured. Ensure docker_client and container_id are in config."

            try:
                path_obj = Path(path)
                if not path_obj.is_absolute():
                    path_obj = Path(working_dir) / path_obj
                content = path_obj.read_text(encoding="utf-8", errors="replace")
                return content[:20000] if len(content) > 20000 else content
            except Exception as e:
                return f"Error reading file: {e}"

        try:
            content = await docker_client.read_file(container_id, path)
            return content[:20000] if len(content) > 20000 else content
        except Exception as e:
            return f"Error reading file: {e}"

    return file_read


def create_file_write_tool():
    """Create file write tool."""

    @tool(args_schema=FileWriteInput)
    async def file_write(
        path: str,
        content: str,
        message: str = "",
        *,
        config: RunnableConfig,
    ) -> str:
        """Write content to a file in the Docker container."""
        configurable = config.get("configurable", {})
        docker_client = configurable.get("docker_client")
        container_id = configurable.get("container_id")
        execution_mode = configurable.get("execution_mode") or os.getenv("EXECUTION_MODE", "docker")
        working_dir = configurable.get("working_dir", "/work")

        if not docker_client or not container_id:
            if execution_mode != "local":
                return "Error: Docker not configured. Ensure docker_client and container_id are in config."

            print(f"  ✏️  Writing: {path}", flush=True)
            try:
                path_obj = Path(path)
                if not path_obj.is_absolute():
                    path_obj = Path(working_dir) / path_obj
                path_obj.parent.mkdir(parents=True, exist_ok=True)
                path_obj.write_text(content, encoding="utf-8")
                return f"Successfully wrote {len(content)} bytes to {path_obj}"
            except Exception as e:
                return f"Error writing file: {e}"

        print(f"  ✏️  Writing: {path}", flush=True)
        try:
            await docker_client.write_file(container_id, path, content)
            return f"Successfully wrote {len(content)} bytes to {path}"
        except Exception as e:
            return f"Error writing file: {e}"

    return file_write


def create_browser_tool():
    """Create web browser/scraping tool."""

    @tool(args_schema=BrowserInput)
    async def browser(
        url: str,
        action: str = "markdown",
        message: str = "",
        *,
        config: RunnableConfig,
    ) -> str:
        """
        Fetch and parse a web page.

        Actions:
        - markdown: Convert HTML to readable markdown
        - html: Get raw HTML
        - links: Extract all links
        - text: Get plain text
        """
        import httpx
        from bs4 import BeautifulSoup

        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; FennecAI/1.0)"
                })
                response.raise_for_status()
                html = response.text
        except Exception as e:
            return f"Error fetching URL: {e}"

        soup = BeautifulSoup(html, "html.parser")

        # Remove scripts + styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        if action == "html":
            return html[:20000]

        elif action == "links":
            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                text = a.get_text(strip=True)[:50]
                links.append(f"[{text}]({href})")
            return "\n".join(links[:100])

        elif action == "text":
            return soup.get_text(separator="\n", strip=True)[:15000]

        else:  # markdown
            # Simple HTML to markdown conversion
            content = []
            for elem in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "pre", "code"]):
                tag = elem.name
                text = elem.get_text(strip=True)
                if not text:
                    continue
                if tag == "h1":
                    content.append(f"# {text}")
                elif tag == "h2":
                    content.append(f"## {text}")
                elif tag == "h3":
                    content.append(f"### {text}")
                elif tag == "h4":
                    content.append(f"#### {text}")
                elif tag == "li":
                    content.append(f"- {text}")
                elif tag in ("pre", "code"):
                    content.append(f"```\n{text}\n```")
                else:
                    content.append(text)

            return "\n\n".join(content)[:15000]

    return browser


def create_web_search_tool():
    """Create web search tool. Uses Tavily API with DuckDuckGo fallback."""

    @tool(args_schema=WebSearchInput)
    async def web_search(
        query: str,
        max_results: int = 5,
        message: str = "",
        *,
        config: RunnableConfig,
    ) -> str:
        """
        Search the web for security research, CVE details, exploit techniques, and tool usage.

        Use this to find:
        - CVE details and proof-of-concept exploits
        - Tool usage guides (nmap flags, sqlmap techniques, etc.)
        - Vulnerability write-ups and disclosures
        - Security advisories
        """
        configurable = config.get("configurable", {})

        # Try Tavily first (better structured results for security research)
        tavily_key = configurable.get("tavily_api_key")
        if not tavily_key:
            import os
            tavily_key = os.environ.get("TAVILY_API_KEY")

        if tavily_key:
            try:
                from tavily import AsyncTavilyClient

                client = AsyncTavilyClient(api_key=tavily_key)
                response = await client.search(
                    query=query,
                    max_results=max_results,
                    search_depth="advanced",
                )
                results = []
                for item in response.get("results", []):
                    title = item.get("title", "")
                    url = item.get("url", "")
                    content = item.get("content", "")
                    results.append(f"### {title}\n{url}\n{content}")
                if results:
                    return "\n\n---\n\n".join(results)
            except Exception:
                pass  # Fall through to DuckDuckGo

        # Fallback: DuckDuckGo (no API key needed)
        try:
            import asyncio
            from ddgs import DDGS

            def _search():
                d = DDGS()
                return list(d.text(query, max_results=max_results))

            raw_results = await asyncio.get_event_loop().run_in_executor(None, _search)
            results = []
            for item in raw_results:
                title = item.get("title", "")
                url = item.get("href", "")
                body = item.get("body", "")
                results.append(f"### {title}\n{url}\n{body}")
            if results:
                return "\n\n---\n\n".join(results)
            return "No results found."
        except Exception as e:
            return f"Search error: {e}"

    return web_search
