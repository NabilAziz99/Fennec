"""
Async Docker client for container management.
"""

import asyncio
import io
import tarfile
from dataclasses import dataclass, field
from typing import Optional

import aiodocker


@dataclass
class ContainerConfig:
    """Configuration for spawning a container."""
    image: str = "fennec-linux" # 
    name: Optional[str] = None
    working_dir: str = "/work"
    network_mode: str = "bridge"
    cap_add: list[str] = field(default_factory=lambda: ["NET_RAW"])
    mem_limit: str = "2g"
    cpu_period: int = 100000
    cpu_quota: int = 100000


@dataclass
class ExecResult:
    """Result of command execution."""
    exit_code: int
    output: str


class DockerClient:
    """Async Docker client wrapper."""

    def __init__(self):
        self._client: Optional[aiodocker.Docker] = None

    async def initialize(self):
        """Initialize the Docker client."""
        self._client = aiodocker.Docker()

    async def close(self):
        """Close the Docker client."""
        if self._client:
            await self._client.close()
            self._client = None

    async def spawn_container(self, config: ContainerConfig) -> str:
        """
        Spawn a new container.

        Returns:
            Container ID
        """
        if not self._client:
            await self.initialize()

        container_config = {
            "Image": config.image,
            "Tty": True,
            "OpenStdin": True,
            "WorkingDir": config.working_dir,
            "HostConfig": {
                "NetworkMode": config.network_mode,
                "CapAdd": config.cap_add,
                "Memory": self._parse_memory(config.mem_limit),
                "CpuPeriod": config.cpu_period,
                "CpuQuota": config.cpu_quota,
            },
        }

        if config.name:
            container_config["name"] = config.name

        container = await self._client.containers.create(config=container_config)
        await container.start()

        return container.id

    def _parse_memory(self, mem_str: str) -> int:
        """Parse memory string to bytes."""
        mem_str = mem_str.lower().strip()
        if mem_str.endswith("g"):
            return int(float(mem_str[:-1]) * 1024 * 1024 * 1024)
        elif mem_str.endswith("m"):
            return int(float(mem_str[:-1]) * 1024 * 1024)
        elif mem_str.endswith("k"):
            return int(float(mem_str[:-1]) * 1024)
        return int(mem_str)

    async def _ensure_running(self, container_id: str) -> None:
        """Ensure a container is running, restarting it if necessary."""
        container = self._client.containers.container(container_id)
        info = await container.show()
        status = info.get("State", {}).get("Status", "unknown")
        if status != "running":
            await container.start()

    async def exec_command(
        self,
        container_id: str,
        command: str,
        cwd: str = "/work",
        timeout: int = 300,
    ) -> ExecResult:
        """Execute a command in a container."""
        if not self._client:
            await self.initialize()

        container = self._client.containers.container(container_id)

        # Ensure the container is running before executing
        try:
            await self._ensure_running(container_id)
        except Exception as e:
            return ExecResult(exit_code=-1, output=f"Failed to ensure container is running: {e}")

        # Wrap command with cd
        full_command = f"cd {cwd} && {command}"

        exec_instance = await container.exec(
            cmd=["bash", "-c", full_command],
            stdout=True,
            stderr=True,
        )

        try:
            async def run_exec():
                output_chunks = []

                # Start execution and get stream
                stream = exec_instance.start(detach=False)

                # Check if it's a coroutine that needs to be awaited
                if asyncio.iscoroutine(stream):
                    stream = await stream

                # Now stream should be the actual stream object
                # Use read_out() method for aiodocker streams
                if hasattr(stream, 'read_out'):
                    while True:
                        msg = await stream.read_out()
                        if msg is None:
                            break
                        if msg.data:
                            output_chunks.append(msg.data)
                elif hasattr(stream, '__aiter__'):
                    async for chunk in stream:
                        if chunk:
                            if isinstance(chunk, bytes):
                                output_chunks.append(chunk)
                            elif hasattr(chunk, 'data'):
                                output_chunks.append(chunk.data)
                else:
                    # Direct bytes result
                    if stream:
                        if isinstance(stream, bytes):
                            output_chunks.append(stream)
                        elif hasattr(stream, 'data'):
                            output_chunks.append(stream.data)

                return b"".join(output_chunks)

            result = await asyncio.wait_for(run_exec(), timeout=timeout)
            output = result.decode("utf-8", errors="replace") if result else ""

            # Get exit code
            exec_info = await exec_instance.inspect()
            exit_code = exec_info.get("ExitCode", 0)

            return ExecResult(exit_code=exit_code, output=output)

        except asyncio.TimeoutError:
            return ExecResult(exit_code=-1, output="Command timed out")
        except Exception as e:
            return ExecResult(exit_code=-1, output=f"Error executing command: {str(e)}")

    async def read_file(self, container_id: str, path: str) -> str:
        """Read a file from the container."""
        if not self._client:
            await self.initialize()

        container = self._client.containers.container(container_id)

        try:
            tar_stream = await container.get_archive(path)

            # Read tar data
            tar_data = b""
            async for chunk in tar_stream:
                tar_data += chunk

            # Extract file content
            tar_buffer = io.BytesIO(tar_data)
            with tarfile.open(fileobj=tar_buffer, mode="r") as tar:
                for member in tar.getmembers():
                    if member.isfile():
                        f = tar.extractfile(member)
                        if f:
                            return f.read().decode("utf-8", errors="replace")

            return ""
        except Exception as e:
            raise RuntimeError(f"Failed to read file: {e}")

    async def write_file(self, container_id: str, path: str, content: str):
        """Write a file to the container."""
        if not self._client:
            await self.initialize()

        container = self._client.containers.container(container_id)

        # Create tar archive with the file
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            file_data = content.encode("utf-8")
            info = tarfile.TarInfo(name=path.split("/")[-1])
            info.size = len(file_data)
            tar.addfile(info, io.BytesIO(file_data))

        tar_buffer.seek(0)

        # Get directory path
        dir_path = "/".join(path.split("/")[:-1]) or "/"

        await container.put_archive(dir_path, tar_buffer.read())

    async def delete_container(self, container_id: str, force: bool = True):
        """Delete a container."""
        if not self._client:
            return

        try:
            container = self._client.containers.container(container_id)
            await container.delete(force=force)
        except Exception:
            pass

    async def cleanup_all(self):
        """Clean up all fennec containers."""
        if not self._client:
            return

        try:
            containers = await self._client.containers.list(all=True)
            for container in containers:
                info = await container.show()
                name = info.get("Name", "")
                if "fennec-" in name:
                    await container.delete(force=True)
        except Exception:
            pass

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
