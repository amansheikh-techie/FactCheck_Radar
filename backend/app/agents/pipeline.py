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
