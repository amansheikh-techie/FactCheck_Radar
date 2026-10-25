"""Unit tests for Pydantic schema validation."""

import pytest
from pydantic import ValidationError

from backend.app.schemas import (
    FactCheckRequest,
    ExtractedClaim,
    ClaimExtractionOutput,
    SearchQuerySet,
    QueryGenerationOutput,
    SourceAssessment,
    SourceAssessmentOutput,
    Citation,
    ClaimVerdict,
    VerdictOutput,
    FactCheckResult,
)


def test_fact_check_request_validation():
    # Valid
    req = FactCheckRequest(input="The moon is made of green cheese.")
    assert req.input == "The moon is made of green cheese."

    # Empty string should fail
    with pytest.raises(ValidationError):
        FactCheckRequest(input="")

    # Too long input should fail (>5000 chars)
    with pytest.raises(ValidationError):
        FactCheckRequest(input="a" * 5001)


def test_claim_extraction_output_schema():
    valid_data = {
        "claims": [
            {"claim": "Water freezes at 0 degrees Celsius.", "category": "scientific"},
            {"claim": "Mount Everest is the tallest mountain above sea level.", "category": "geographical"},
        ]
    }
    output = ClaimExtractionOutput.model_validate(valid_data)
    assert len(output.claims) == 2
    assert output.claims[0].category == "scientific"

    # Empty claims list should fail (min_length=1)
    with pytest.raises(ValidationError):
        ClaimExtractionOutput.model_validate({"claims": []})

    # More than 3 claims should fail (max_length=3)
    with pytest.raises(ValidationError):
        ClaimExtractionOutput.model_validate({
            "claims": [{"claim": f"claim {i}", "category": "test"} for i in range(4)]
        })


def test_query_generation_output_schema():
    valid_data = {
        "search_queries": [
            {"claim_index": 0, "queries": ["water freezing point celsius", "at what temperature does water freeze"]},
        ]
    }
    output = QueryGenerationOutput.model_validate(valid_data)
    assert len(output.search_queries) == 1
    assert len(output.search_queries[0].queries) == 2


def test_source_assessment_schema():
    valid_data = {
        "claim_index": 0,
        "assessments": [
            {
                "url": "https://example.com/water",
                "domain": "example.com",
                "title": "Water Properties",
                "snippet": "Pure water freezes at 0 °C (32 °F) at standard atmospheric pressure.",
                "stance": "supports",
                "reason": "Explicitly confirms that water freezes at 0 degrees Celsius.",
            }
        ]
    }
    output = SourceAssessmentOutput.model_validate(valid_data)
    assert len(output.assessments) == 1
    assert output.assessments[0].stance == "supports"

    # Invalid stance should fail
    with pytest.raises(ValidationError):
        SourceAssessmentOutput.model_validate({
            "claim_index": 0,
            "assessments": [{
                "url": "https://example.com",
                "domain": "example.com",
                "title": "Title",
                "snippet": "Snippet",
                "stance": "invalid-stance",
                "reason": "Reason",
            }]
        })


def test_verdict_output_schema():
    valid_data = {
        "verdicts": [
            {
                "claim": "Water freezes at 0 degrees Celsius.",
                "verdict": "True",
                "confidence": 99,
                "explanation": "Standard physical chemistry universally confirms this temperature at sea level.",
                "citations": [
                    {
                        "number": 1,
                        "url": "https://example.com/water",
                        "domain": "example.com",
                        "title": "Water Properties",
                        "stance": "supports",
                    }
                ]
            }
        ]
    }
    output = VerdictOutput.model_validate(valid_data)
    assert len(output.verdicts) == 1
    assert output.verdicts[0].verdict == "True"
    assert output.verdicts[0].confidence == 99

    # Confidence out of bounds (>100 or <0) should fail
    with pytest.raises(ValidationError):
        ClaimVerdict(
            claim="Test",
            verdict="True",
            confidence=105,
            explanation="Test",
            citations=[],
        )


def test_fact_check_result_schema():
    result = FactCheckResult(
        input="Water freezes at 0 C",
        claim_verdicts=[
            ClaimVerdict(
                claim="Water freezes at 0 C",
                verdict="True",
                confidence=98,
                explanation="Verified by physical science sources.",
                citations=[
                    Citation(
                        number=1,
                        url="https://example.com",
                        domain="example.com",
                        title="Water Facts",
                        stance="supports",
                    )
                ],
            )
        ],
        model_fast="nvidia/Nemotron-3-Nano-30B-A3B",
        model_reasoning="nvidia/Nemotron-3-Ultra-550b-a55b",
    )
    assert result.input == "Water freezes at 0 C"
    assert result.timestamp is not None
    assert len(result.claim_verdicts) == 1
