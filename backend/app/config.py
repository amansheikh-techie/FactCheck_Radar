"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """All config loaded from .env or environment variables."""

    # Active LLM Provider: "nvidia" (default) or "nebius"
    llm_provider: str = Field(
        default="nvidia",
        description="Active LLM provider: 'nvidia' (default) or 'nebius'",
    )

    # Nebius Token Factory
    nebius_api_key: str = Field(default="", description="Nebius Token Factory API key")
    nebius_base_url: str = Field(
        default="https://api.tokenfactory.nebius.com/v1/",
        description="OpenAI-compatible base URL for Nebius Token Factory",
    )
    nebius_model_fast: str = Field(
        default="nvidia/Nemotron-3-Nano-30B-A3B",
        description="Fast model for Nebius provider",
    )
    nebius_model_reasoning: str = Field(
        default="nvidia/Nemotron-3-Ultra-550b-a55b",
        description="Reasoning model for Nebius provider",
    )

    # NVIDIA Build NIM API
    nvidia_api_key: str = Field(default="", description="NVIDIA Build API key")
    nvidia_base_url: str = Field(
        default="https://integrate.api.nvidia.com/v1",
        description="OpenAI-compatible base URL for NVIDIA Build API",
    )
    nvidia_model_fast: str = Field(
        default="nvidia/nemotron-3.5-lightning-30b-a3b",
        description="Fast model for NVIDIA provider",
    )
    nvidia_model_reasoning: str = Field(
        default="nvidia/nemotron-3.5-lightning-30b-a3b",
        description="Reasoning model for NVIDIA provider (lightning-30b for sub-30s speed)",
    )

    # Tavily
    tavily_api_key: str = Field(default="", description="Tavily API key for web search")

    # Timeouts
    llm_request_timeout: float = Field(default=35.0, description="Per-request LLM timeout in seconds")
    pipeline_timeout: float = Field(default=45.0, description="Total pipeline execution timeout in seconds")

    # Optional generic overrides across providers
    model_fast: str = Field(
        default="",
        description="Override fast model regardless of provider",
    )
    model_reasoning: str = Field(
        default="",
        description="Override reasoning model regardless of provider",
    )

    # Explicit Demo Mode flag (default False - never silent fallback)
    demo_mode: bool = Field(
        default=False,
        description="Explicit demo mode flag",
    )

    # Fallback model candidates (tried in order if primary is unavailable)
    model_fast_fallbacks: list[str] = Field(
        default=[
            "nvidia/nemotron-3.5-lightning-30b-a3b",
            "nvidia/nemotron-3.5-bolt-e4b",
            "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
            "nvidia/llama-3.1-nemotron-70b-instruct",
            "nvidia/Nemotron-3-Nano-30B-A3B",
            "nvidia/nemotron-3-super-120b-a12b",
            "nvidia/Nemotron-3_5-Lightning",
        ]
    )
    model_reasoning_fallbacks: list[str] = Field(
        default=[
            "nvidia/nemotron-3.5-lightning-30b-a3b",
            "nvidia/nemotron-3-ultra-550b-a55b",
            "nvidia/Nemotron-3-Ultra-550b-a55b",
            "nvidia/nemotron-3.5-super-vl-120b-a12b",
            "nvidia/nemotron-4-340b-instruct",
            "nvidia/nemotron-3-super-120b-a12b",
            "nvidia/llama-3.1-nemotron-70b-instruct",
        ]
    )

    # Operational
    cache_ttl_seconds: int = Field(default=900, description="Cache TTL in seconds")
    max_input_length: int = Field(default=5000, description="Max input length in chars")
    max_cache_entries: int = Field(default=100, description="Max cache entries")

    # Networking & Security
    allowed_origins: str = Field(
        default="http://localhost:8000,http://127.0.0.1:8000",
        description="Comma-separated allowed CORS origins (default same-origin local)",
    )
    port: int = Field(default=8000, description="Server port")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Singleton
settings = Settings()
