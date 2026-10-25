"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """All config loaded from .env or environment variables."""

    # Nebius Token Factory
    nebius_api_key: str = Field(default="", description="Nebius Token Factory API key")
    nebius_base_url: str = Field(
        default="https://api.tokenfactory.nebius.com/v1",
        description="OpenAI-compatible base URL for Nebius Token Factory",
    )

    # Tavily
    tavily_api_key: str = Field(default="", description="Tavily API key for web search")

    # Model IDs
    model_fast: str = Field(
        default="nvidia/Nemotron-3-Nano-30B-A3B",
        description="Fast model for claim extraction, query gen, source assessment",
    )
    model_reasoning: str = Field(
        default="nvidia/Nemotron-3-Ultra-550b-a55b",
        description="Reasoning model for final verdict",
    )

    # Fallback model IDs (tried in order if primary is unavailable)
    model_fast_fallbacks: list[str] = Field(
        default=[
            "nvidia/nemotron-3-super-120b-a12b",
            "nvidia/Nemotron-3_5-Lightning",
        ]
    )
    model_reasoning_fallbacks: list[str] = Field(
        default=[
            "nvidia/nemotron-3-super-120b-a12b",
        ]
    )

    # Operational
    cache_ttl_seconds: int = Field(default=900, description="Cache TTL in seconds")
    max_input_length: int = Field(default=5000, description="Max input length in chars")
    max_cache_entries: int = Field(default=100, description="Max cache entries")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Singleton
settings = Settings()
