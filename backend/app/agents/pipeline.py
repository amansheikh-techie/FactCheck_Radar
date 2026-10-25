"""Main agent pipeline: orchestrates all steps and yields SSE events."""

from __future__ import annotations

import json
import logging
from typing import AsyncGenerator

from backend.app.schemas import (
    ClaimExtractionOutput,
    ClaimVerdict,
    ErrorEvent,
    ExtractedClaim,
    FactCheckResult,
    QueryGenerationOutput,
    SourceAssessment,
    SourceAssessmentOutput,
    StepEvent,
    VerdictOutput,
)
from backend.app.services.nebius_client import nebius_client
from backend.app.services.tavily_service import tavily_service, SearchResult
from backend.app.services.url_extractor import extract_text_from_url, is_url
from backend.app.agents.prompts import (
    CLAIM_EXTRACTION_SYSTEM,
    CLAIM_EXTRACTION_USER,
    QUERY_GENERATION_SYSTEM,
    QUERY_GENERATION_USER,
    SOURCE_ASSESSMENT_SYSTEM,
    SOURCE_ASSESSMENT_USER,
    VERDICT_SYSTEM,
    VERDICT_USER,
)

logger = logging.getLogger(__name__)


async def run_factcheck_pipeline(
    user_input: str,
) -> AsyncGenerator[str, None]:
    """
    Run the full fact-check pipeline.
    Yields Server-Sent Event lines (data: {...}).
    """

    def sse(event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    fast_model = nebius_client.fast_model
    reasoning_model = nebius_client.reasoning_model

    try:
        # ── Step 0: URL extraction (if needed) ────────────
        text = user_input
        if is_url(user_input.strip()):
            yield sse("step", {"step": "fetching_url", "message": "Fetching and extracting article text..."})
            try:
                text = await extract_text_from_url(user_input.strip())
            except ValueError as exc:
                yield sse("error", {"message": str(exc)})
                return

        # ── Step 1: Claim extraction ──────────────────────
        yield sse("step", {"step": "extracting_claims", "message": "Extracting checkable claims..."})

        claims_output: ClaimExtractionOutput = await nebius_client.chat_json(
            model=fast_model,
            system_prompt=CLAIM_EXTRACTION_SYSTEM,
            user_prompt=CLAIM_EXTRACTION_USER.format(text=text[:3000]),
            output_schema=ClaimExtractionOutput,
        )

        claims = claims_output.claims
        yield sse("claims", {"claims": [c.model_dump() for c in claims]})
        logger.info("Extracted %d claims", len(claims))

        if not claims:
            yield sse("step", {"step": "done", "message": "No checkable claims detected."})
            fallback_result = FactCheckResult(
                input=user_input,
                claim_verdicts=[
                    ClaimVerdict(
                        claim=user_input[:200],
                        verdict="Unverifiable",
                        confidence=0,
                        explanation="No specific, checkable factual claims could be extracted from the input text.",
                        citations=[],
                    )
                ],
                model_fast=fast_model,
                model_reasoning=reasoning_model,
            )
            yield sse("result", fallback_result.model_dump())
            return

        # ── Step 2: Query generation ──────────────────────
        yield sse("step", {"step": "generating_queries", "message": "Generating search queries..."})

        claims_json = json.dumps(
            [{"index": i, "claim": c.claim} for i, c in enumerate(claims)],
            indent=2,
        )
        queries_output: QueryGenerationOutput = await nebius_client.chat_json(
            model=fast_model,
            system_prompt=QUERY_GENERATION_SYSTEM,
            user_prompt=QUERY_GENERATION_USER.format(claims_json=claims_json),
            output_schema=QueryGenerationOutput,
        )

        # ── Step 3: Evidence retrieval via Tavily ─────────
        yield sse("step", {"step": "searching", "message": "Searching the web for evidence..."})

        # Organize search results by claim
        evidence_by_claim: dict[int, list[SearchResult]] = {}
        for qset in queries_output.search_queries:
            idx = qset.claim_index
            results = await tavily_service.search_multiple(qset.queries)
            evidence_by_claim[idx] = results
            logger.info(
                "Claim %d: %d results from %d queries",
                idx, len(results), len(qset.queries),
            )

        # ── Step 4: Source assessment ─────────────────────
        yield sse("step", {"step": "assessing_sources", "message": "Reading and assessing sources..."})

        assessed_evidence: dict[int, list[SourceAssessment]] = {}
        for idx, claim in enumerate(claims):
            sources = evidence_by_claim.get(idx, [])
            if not sources:
                assessed_evidence[idx] = []
                continue

            sources_json = json.dumps(
                [
                    {
                        "url": s.url,
                        "domain": s.domain,
                        "title": s.title,
                        "snippet": s.snippet,
                    }
                    for s in sources
                ],
                indent=2,
            )

            assessment: SourceAssessmentOutput = await nebius_client.chat_json(
                model=fast_model,
                system_prompt=SOURCE_ASSESSMENT_SYSTEM,
                user_prompt=SOURCE_ASSESSMENT_USER.format(
                    claim_index=idx,
                    claim=claim.claim,
                    sources_json=sources_json,
                ),
                output_schema=SourceAssessmentOutput,
            )
            assessed_evidence[idx] = assessment.assessments

        # ── Step 5: Verdict generation ────────────────────
        yield sse("step", {"step": "reasoning", "message": "Reasoning about the evidence..."})

        # Build evidence summary for the reasoning model
        evidence_summary = []
        for idx, claim in enumerate(claims):
            assessments = assessed_evidence.get(idx, [])
            evidence_summary.append({
                "claim_index": idx,
                "claim": claim.claim,
                "category": claim.category,
                "evidence": [
                    {
                        "url": a.url,
                        "domain": a.domain,
                        "title": a.title,
                        "snippet": a.snippet,
                        "stance": a.stance,
                        "reason": a.reason,
                    }
                    for a in assessments
                ],
            })

        verdict_output: VerdictOutput = await nebius_client.chat_json(
            model=reasoning_model,
            system_prompt=VERDICT_SYSTEM,
            user_prompt=VERDICT_USER.format(
                evidence_json=json.dumps(evidence_summary, indent=2)
            ),
            output_schema=VerdictOutput,
            max_tokens=4096,
        )

        # ── Build final result ────────────────────────────
        result = FactCheckResult(
            input=user_input,
            claim_verdicts=verdict_output.verdicts,
            model_fast=fast_model,
            model_reasoning=reasoning_model,
        )

        yield sse("step", {"step": "done", "message": "Fact-check complete!"})
        yield sse("result", result.model_dump())

    except Exception as exc:
        logger.exception("Pipeline error: %s", exc)
        yield sse("error", {"message": f"An error occurred: {str(exc)}"})


async def run_demo_pipeline(user_input: str) -> AsyncGenerator[str, None]:
    """
    Simulated pipeline for interactive demonstrations and recording video.
    Emits genuine SSE step transitions and realistic fact-check verdicts with citations.
    """
    import asyncio

    def sse(event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    fast_model = "nvidia/Nemotron-3-Nano-30B-A3B"
    reasoning_model = "nvidia/Nemotron-3-Ultra-550b-a55b"

    await asyncio.sleep(0.5)
    yield sse("step", {"step": "extracting_claims", "message": "Extracting checkable claims with Nemotron Nano..."})
    await asyncio.sleep(1.0)

    input_lower = user_input.lower()
    if "great wall" in input_lower or "china" in input_lower:
        claim_text = "The Great Wall of China is visible from space with the naked eye."
        category = "geographical"
        verdict = "False"
        confidence = 96
        explanation = (
            "NASA astronauts and high-resolution satellite imagery confirm that the Great Wall of China "
            "cannot be seen from low Earth orbit with the naked eye due to its narrow width and optical blending "
            "with surrounding terrain. This widespread belief originated in pre-spaceflight literature."
        )
        citations = [
            {"number": 1, "url": "https://www.nasa.gov/vision/space/workinginspace/great_wall.html", "domain": "nasa.gov", "title": "China's Wall Less Great in View from Space", "stance": "contradicts"},
            {"number": 2, "url": "https://www.scientificamerican.com/article/is-chinas-great-wall-visible-from-space/", "domain": "scientificamerican.com", "title": "Is China's Great Wall Visible from Space?", "stance": "contradicts"},
            {"number": 3, "url": "https://en.wikipedia.org/wiki/Great_Wall_of_China#Visibility_from_space", "domain": "wikipedia.org", "title": "Visibility from Space - Great Wall of China", "stance": "contradicts"},
        ]
    elif "flat" in input_lower or "earth" in input_lower:
        claim_text = "The Earth is flat and gravity is an illusion."
        category = "scientific"
        verdict = "False"
        confidence = 99
        explanation = (
            "Centuries of astronomical observations, circumnavigation, geodetic satellite measurements, and space imagery "
            "definitively confirm the Earth is an oblate spheroid. Gravitational attraction governs planetary mass and orbit."
        )
        citations = [
            {"number": 1, "url": "https://science.nasa.gov/earth/facts/", "domain": "nasa.gov", "title": "Earth Facts & Measurements", "stance": "contradicts"},
            {"number": 2, "url": "https://www.noaa.gov/education/resource-collections/ocean-coasts/earth-shape", "domain": "noaa.gov", "title": "Geodesy and Earth's Oblate Shape", "stance": "contradicts"},
        ]
    elif "water" in input_lower or "boil" in input_lower:
        claim_text = "Water boils at 100 degrees Celsius at sea level."
        category = "scientific"
        verdict = "True"
        confidence = 100
        explanation = (
            "Under standard atmospheric pressure (1 atm / 101.325 kPa) at sea level, pure water boils at 100 °C (212 °F). "
            "Thermodynamic standards and chemical literature consistently verify this baseline phase transition."
        )
        citations = [
            {"number": 1, "url": "https://www.nist.gov/pml/weights-and-measures/metric-si/temperature", "domain": "nist.gov", "title": "NIST Temperature Standards and Boiling Point", "stance": "supports"},
            {"number": 2, "url": "https://www.usgs.gov/special-topics/water-science-school/science/water-boiling-points", "domain": "usgs.gov", "title": "The Temperature of Water - Boiling Points", "stance": "supports"},
        ]
    else:
        claim_text = user_input.strip()[:150]
        category = "general"
        verdict = "Mostly True"
        confidence = 88
        explanation = (
            f"Cross-referencing authoritative databases indicates that '{claim_text}' is supported by verified reporting, "
            "with minor contextual nuances noted across independent sources."
        )
        citations = [
            {"number": 1, "url": "https://www.reuters.com/fact-check", "domain": "reuters.com", "title": "Reuters Fact Check Index", "stance": "supports"},
            {"number": 2, "url": "https://apnews.com/hub/ap-fact-check", "domain": "apnews.com", "title": "Associated Press Verification", "stance": "supports"},
        ]

    yield sse("claims", {"claims": [{"claim": claim_text, "category": category}]})
    await asyncio.sleep(0.8)

    yield sse("step", {"step": "generating_queries", "message": "Generating neutral search queries..."})
    await asyncio.sleep(0.9)

    yield sse("step", {"step": "searching", "message": "Searching the web for cross-source evidence (Tavily)..."})
    await asyncio.sleep(1.2)

    yield sse("step", {"step": "assessing_sources", "message": "Evaluating credibility & source stances with Nemotron Nano..."})
    await asyncio.sleep(1.0)

    yield sse("step", {"step": "reasoning", "message": "Nemotron Ultra 550B synthesizing evidence & calibrating confidence..."})
    await asyncio.sleep(1.3)

    final_result = {
        "input": user_input,
        "claim_verdicts": [
            {
                "claim": claim_text,
                "verdict": verdict,
                "confidence": confidence,
                "explanation": explanation,
                "citations": citations,
            }
        ],
        "model_fast": fast_model,
        "model_reasoning": reasoning_model,
    }

    yield sse("step", {"step": "done", "message": "Fact-check complete!"})
    yield sse("result", final_result)
