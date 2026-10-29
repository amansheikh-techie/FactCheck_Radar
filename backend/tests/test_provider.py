"""Unit tests for LLM provider configuration and fail-fast validation."""

import pytest
from unittest.mock import patch

from backend.app.config import Settings
from backend.app.services.nebius_client import LLMClient, _is_placeholder
from backend.app.schemas import FactCheckResult, ClaimVerdict, Citation


def test_is_placeholder():
    assert _is_placeholder("") is True
    assert _is_placeholder(None) is True
    assert _is_placeholder("your_api_key_here") is True
    assert _is_placeholder("YOUR-KEY") is True
    assert _is_placeholder("placeholder") is True
    assert _is_placeholder("<enter_key>") is True
    assert _is_placeholder("short") is True
    assert _is_placeholder("nvapi-dummy_test_key_sample") is False


def test_provider_defaults_to_nvidia():
    s = Settings(llm_provider="nvidia")
    assert s.llm_provider == "nvidia"
    assert s.nvidia_base_url == "https://integrate.api.nvidia.com/v1"
    assert s.nebius_base_url.startswith("https://api.tokenfactory.nebius.com/v1")


def test_fail_fast_on_missing_or_placeholder_key():
    with patch("backend.app.services.nebius_client.settings") as mock_settings:
        mock_settings.llm_provider = "nebius"
        mock_settings.nebius_api_key = "your_nebius_key_here"
        mock_settings.nebius_base_url = "https://api.tokenfactory.nebius.com/v1/"
        mock_settings.nebius_model_fast = "nvidia/Nemotron-3-Nano-30B-A3B"
        mock_settings.nebius_model_reasoning = "nvidia/Nemotron-3-Ultra-550b-a55b"
        mock_settings.model_fast = ""
        mock_settings.model_reasoning = ""

        client = LLMClient()
        with pytest.raises(RuntimeError) as exc_info:
            client.validate_configuration()
        assert "NEBIUS_API_KEY" in str(exc_info.value)
        assert "missing or still a placeholder" in str(exc_info.value)


def test_fact_check_result_schema_provider_fields():
    res = FactCheckResult(
        input="Water boils at 100 C",
        claim_verdicts=[
            ClaimVerdict(
                claim="Water boils at 100 C",
                verdict="True",
                confidence=100,
                explanation="Standard thermodynamic observation.",
                citations=[
                    Citation(
                        number=1,
                        url="https://usgs.gov",
                        domain="usgs.gov",
                        title="Water facts",
                        stance="supports",
                    )
                ],
            )
        ],
        provider="nvidia",
        models_used={
            "fast": "nvidia/nemotron-3.5-lightning-30b-a3b",
            "reasoning": "nvidia/nemotron-3-ultra-550b-a55b",
        },
        model_fast="nvidia/nemotron-3.5-lightning-30b-a3b",
        model_reasoning="nvidia/nemotron-3-ultra-550b-a55b",
        is_live=True,
    )
    assert res.provider == "nvidia"
    assert res.models_used["fast"] == "nvidia/nemotron-3.5-lightning-30b-a3b"
    assert res.is_live is True
