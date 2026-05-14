"""
Configuration settings using pydantic-settings.
"""

import os
from functools import lru_cache
from typing import Literal, Optional

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env into os.environ so validators and get_default_llm() work
# regardless of how the app is launched (CLI, API, LangGraph Studio).
load_dotenv()


class FennecConfig(BaseSettings):
    """Fennec AI configuration with environment variable support."""

    model_config = SettingsConfigDict(
        env_prefix="FENNEC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Configuration
    llm_provider: Literal["anthropic", "openai", "openrouter"] = "anthropic"
    llm_model: str = "claude-sonnet-4-20250514"
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    @field_validator("llm_provider", mode="before")
    @classmethod
    def get_llm_provider(cls, v):
        # Prioritize env var without prefix
        env_val = os.environ.get("LLM_PROVIDER")
        if env_val:
            return env_val
        return v or "anthropic"

    @field_validator("llm_model", mode="before")
    @classmethod
    def get_llm_model(cls, v):
        # Prioritize env var without prefix
        env_val = os.environ.get("LLM_MODEL")
        if env_val:
            return env_val
        return v or "claude-sonnet-4-20250514"

    @field_validator("openrouter_api_key", mode="before")
    @classmethod
    def get_openrouter_key(cls, v):
        # Prioritize env var without prefix
        env_val = os.environ.get("OPENROUTER_API_KEY")
        if env_val:
            return env_val
        return v

    # Per-agent model overrides (fall back to llm_model if not set)
    recon_llm_model: Optional[str] = None
    analyst_llm_model: Optional[str] = None
    pentester_llm_model: Optional[str] = None

    @field_validator("recon_llm_model", mode="before")
    @classmethod
    def get_recon_model(cls, v):
        return os.environ.get("RECON_LLM_MODEL") or v or None

    @field_validator("analyst_llm_model", mode="before")
    @classmethod
    def get_analyst_model(cls, v):
        return os.environ.get("ANALYST_LLM_MODEL") or v or None

    @field_validator("pentester_llm_model", mode="before")
    @classmethod
    def get_pentester_model(cls, v):
        return os.environ.get("PENTESTER_LLM_MODEL") or v or None

    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096
    # Hard timeout (seconds) for LLM API calls. Prevents hangs on slow/partial responses.
    llm_timeout: int = 60
    # Provider/client-level retries for transient failures.
    llm_max_retries: int = 2

    # API Keys - also read from standard env vars
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    @field_validator("anthropic_api_key", mode="before")
    @classmethod
    def get_anthropic_key(cls, v):
        return v or os.environ.get("ANTHROPIC_API_KEY")

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def get_openai_key(cls, v):
        return v or os.environ.get("OPENAI_API_KEY")

    # Search API Keys
    tavily_api_key: Optional[str] = None
    perplexity_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    google_cx_key: Optional[str] = None
    searxng_url: Optional[str] = None

    # Docker Configuration
    docker_image: str = "fennec-linux" # kalilinux/kali-rolling:latest
    docker_network: str = "bridge"
    docker_memory_limit: str = "2g"
    docker_cpu_limit: float = 1.0

    # Timeouts
    command_timeout: int = 300  # 5 minutes
    search_timeout: int = 30

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Memory
    embedding_model: str = "text-embedding-3-small"
    memory_score_threshold: float = 0.2


# Assessment method presets (Turbo / Balanced / Deep)
METHOD_PRESETS = {
    "turbo": {
        "recon_model_calls": 10,
        "analyst_model_calls": 8,
        "pentester_model_calls": 15,
        "task_timeout": 1800,       # 30 minutes
        "recursion_limit": 150,
    },
    "balanced": {
        "recon_model_calls": 15,
        "analyst_model_calls": 15,
        "pentester_model_calls": 30,
        "task_timeout": 3600,       # 1 hour
        "recursion_limit": 300,
    },
    "deep": {
        "recon_model_calls": 25,
        "analyst_model_calls": 25,
        "pentester_model_calls": 60,
        "task_timeout": 7200,       # 2 hours
        "recursion_limit": 600,
    },
}


def get_method_preset(method: str) -> dict:
    """Get configuration preset for an assessment method."""
    return METHOD_PRESETS.get(method, METHOD_PRESETS["balanced"])


@lru_cache
def get_config() -> FennecConfig:
    """Get cached configuration instance."""
    return FennecConfig()


_llm_instance = None
_docker_session = None  # {"docker_client": ..., "container_id": ...}


def get_default_llm():
    """Create an LLM from config settings.

    Used as a fallback when the LLM isn't injected into RunnableConfig
    (e.g. when running from LangGraph Studio).
    """
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    config = get_config()

    if config.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        _llm_instance = ChatAnthropic(
            model=config.llm_model,
            api_key=config.anthropic_api_key,
            temperature=config.llm_temperature,
            max_tokens=config.llm_max_tokens,
            timeout=config.llm_timeout,
        )
    elif config.llm_provider == "openrouter":
        from langchain_openai import ChatOpenAI
        _llm_instance = ChatOpenAI(
            model=config.llm_model,
            api_key=config.openrouter_api_key,
            base_url=config.openrouter_base_url,
            temperature=config.llm_temperature,
            max_tokens=config.llm_max_tokens,
            timeout=config.llm_timeout,
            max_retries=config.llm_max_retries,
            default_headers={
                "HTTP-Referer": "https://fennec.ai",
                "X-Title": "Fennec AI",
            },
        )
    else:
        from langchain_openai import ChatOpenAI
        _llm_instance = ChatOpenAI(
            model=config.llm_model,
            api_key=config.openai_api_key,
            temperature=config.llm_temperature,
            max_tokens=config.llm_max_tokens,
            timeout=config.llm_timeout,
            max_retries=config.llm_max_retries,
        )

    return _llm_instance


def create_llm(model: str):
    """Create an LLM instance for a specific model.

    Uses the same provider/credentials as the default LLM,
    but with a different model name. Used for per-agent model overrides.
    """
    config = get_config()

    if config.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model,
            api_key=config.anthropic_api_key,
            temperature=config.llm_temperature,
            max_tokens=config.llm_max_tokens,
            timeout=config.llm_timeout,
        )
    elif config.llm_provider == "openrouter":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            api_key=config.openrouter_api_key,
            base_url=config.openrouter_base_url,
            temperature=config.llm_temperature,
            max_tokens=config.llm_max_tokens,
            timeout=config.llm_timeout,
            max_retries=config.llm_max_retries,
            default_headers={
                "HTTP-Referer": "https://fennec.ai",
                "X-Title": "Fennec AI",
            },
        )
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            api_key=config.openai_api_key,
            temperature=config.llm_temperature,
            max_tokens=config.llm_max_tokens,
            timeout=config.llm_timeout,
            max_retries=config.llm_max_retries,
        )


async def get_default_docker() -> dict:
    """Get or create a shared Docker session (client + container).

    Used as a fallback when docker_client/container_id aren't injected
    into RunnableConfig (e.g. when running from LangGraph Studio).

    Returns dict with 'docker_client' and 'container_id'.
    """
    global _docker_session
    if _docker_session is not None:
        return _docker_session

    from ..docker.client import DockerClient, ContainerConfig
    import uuid

    config = get_config()
    client = DockerClient()
    await client.initialize()

    container_config = ContainerConfig(
        image=config.docker_image,
        name=f"fennec-studio-{uuid.uuid4().hex[:8]}",
    )
    container_id = await client.spawn_container(container_config)

    _docker_session = {
        "docker_client": client,
        "container_id": container_id,
    }
    return _docker_session
