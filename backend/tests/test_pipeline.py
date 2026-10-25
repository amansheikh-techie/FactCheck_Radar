"""Unit tests for the agent pipeline with mocked LLM and Tavily responses."""

import json
import pytest
from unittest.mock import AsyncMock, patch

from backend.app.schemas import (
    ClaimExtractionOutput,
    ExtractedClaim,
    QueryGenerationOutput,
    SearchQuerySet,
    SourceAssessmentOutput,
    SourceAssessment,
    VerdictOutput,
    ClaimVerdict,
    Citation,
)
from backend.app.services.tavily_service import SearchResult
from backend.app.agents.pipeline import run_factcheck_pipeline


@pytest.mark.asyncio
async def test_run_factcheck_pipeline_mocked():
    # 1. Mock outputs
    mock_claims = ClaimExtractionOutput(
        claims=[
            ExtractedClaim(
                claim="Water boils at 100 degrees Celsius at sea level.",
                category="scientific",
            )
        ]
    )

    mock_queries = QueryGenerationOutput(
        search_queries=[
            SearchQuerySet(
                claim_index=0,
                queries=["water boiling temperature 100 celsius sea level"],
            )
        ]
    )

    mock_search_results = [
        SearchResult(
            title="Boiling Point of Water",
            url="https://usgs.gov/water-boiling",
            domain="usgs.gov",
            snippet="At sea level, water boils at 100 °C (212 °F).",
            score=0.95,
        )
    ]

    mock_assessment = SourceAssessmentOutput(
        claim_index=0,
        assessments=[
            SourceAssessment(
                url="https://usgs.gov/water-boiling",
                domain="usgs.gov",
                title="Boiling Point of Water",
                snippet="At sea level, water boils at 100 °C (212 °F).",
                stance="supports",
                reason="Directly confirms the 100 C boiling point at sea level.",
            )
        ],
    )

    mock_verdicts = VerdictOutput(
        verdicts=[
            ClaimVerdict(
                claim="Water boils at 100 degrees Celsius at sea level.",
                verdict="True",
                confidence=99,
                explanation="Established thermodynamics and official geological survey data verify that water boils at 100 C at standard sea-level atmospheric pressure.",
                citations=[
                    Citation(
                        number=1,
                        url="https://usgs.gov/water-boiling",
                        domain="usgs.gov",
                        title="Boiling Point of Water",
                        stance="supports",
                    )
                ],
            )
        ]
    )

    # Mock chat_json returns
    async def mock_chat_json(model, system_prompt, user_prompt, output_schema, **kwargs):
        if output_schema == ClaimExtractionOutput:
            return mock_claims
        elif output_schema == QueryGenerationOutput:
            return mock_queries
        elif output_schema == SourceAssessmentOutput:
            return mock_assessment
        elif output_schema == VerdictOutput:
            return mock_verdicts
        raise ValueError(f"Unexpected schema: {output_schema}")

    with patch(
        "backend.app.agents.pipeline.nebius_client.chat_json",
        side_effect=mock_chat_json,
    ), patch(
        "backend.app.agents.pipeline.tavily_service.search_multiple",
        new=AsyncMock(return_value=mock_search_results),
    ):
        events = []
        async for line in run_factcheck_pipeline("Water boils at 100 C at sea level"):
            events.append(line)

        assert len(events) > 0

        # Check for step events
        step_events = [e for e in events if "event: step" in e]
        assert any("extracting_claims" in e for e in step_events)
        assert any("generating_queries" in e for e in step_events)
        assert any("searching" in e for e in step_events)
        assert any("assessing_sources" in e for e in step_events)
        assert any("reasoning" in e for e in step_events)
        assert any("done" in e for e in step_events)

        # Check for claims event
        claims_events = [e for e in events if "event: claims" in e]
        assert len(claims_events) == 1
        claims_data = json.loads(claims_events[0].split("data: ")[1])
        assert claims_data["claims"][0]["category"] == "scientific"

        # Check for final result event
        result_events = [e for e in events if "event: result" in e]
        assert len(result_events) == 1
        result_data = json.loads(result_events[0].split("data: ")[1])
        assert result_data["claim_verdicts"][0]["verdict"] == "True"
        assert result_data["claim_verdicts"][0]["confidence"] == 99
