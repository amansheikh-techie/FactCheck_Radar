"""Pydantic schemas for API request/response and LLM structured outputs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# API Request
# ──────────────────────────────────────────────

class FactCheckRequest(BaseModel):
    """Incoming fact-check request from the frontend."""
    input: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="A claim, headline, or URL to fact-check",
    )


# ──────────────────────────────────────────────
# LLM Output Schemas (strict JSON parsing)
# ──────────────────────────────────────────────

class ExtractedClaim(BaseModel):
    """A single checkable claim extracted from the input."""
    claim: str = Field(..., description="A single, specific, checkable factual claim")
    category: str = Field(..., description="Category: scientific, political, statistical, historical, health, other")


class ClaimExtractionOutput(BaseModel):
    """Output of the claim extraction step."""
    claims: list[ExtractedClaim] = Field(
        ..., min_length=1, max_length=3,
        description="Up to 3 distinct checkable claims",
    )


class SearchQuerySet(BaseModel):
    """Search queries for one claim."""
    claim_index: int = Field(..., ge=0, description="Index of the claim (0-based)")
    queries: list[str] = Field(
        ..., min_length=1, max_length=2,
        description="1-2 neutral, unbiased search queries",
    )


class QueryGenerationOutput(BaseModel):
    """Output of the query generation step."""
    search_queries: list[SearchQuerySet]


StanceType = Literal["supports", "contradicts", "neutral"]


class SourceAssessment(BaseModel):
    """Assessment of a single source's stance on a claim."""
    url: str
    domain: str
    title: str
    snippet: str
    stance: StanceType
    reason: str = Field(..., description="One-sentence justification for the stance label")


class SourceAssessmentOutput(BaseModel):
    """Output of the source assessment step for one claim."""
    claim_index: int = Field(..., ge=0)
    assessments: list[SourceAssessment]


VerdictLabel = Literal[
    "True", "Mostly True", "Mixed", "Mostly False", "False", "Unverifiable"
]


class Citation(BaseModel):
    """A numbered citation linking to a source."""
    number: int = Field(..., ge=1)
    url: str
    domain: str
    title: str
    stance: StanceType


class ClaimVerdict(BaseModel):
    """Verdict for a single claim."""
    claim: str
    verdict: VerdictLabel
    confidence: int = Field(..., ge=0, le=100)
    explanation: str = Field(..., description="2-3 sentence explanation of the verdict")
    citations: list[Citation]


class VerdictOutput(BaseModel):
    """Output of the verdict generation step."""
    verdicts: list[ClaimVerdict]


# ──────────────────────────────────────────────
# Final API Response
# ──────────────────────────────────────────────

class FactCheckResult(BaseModel):
    """Complete fact-check result returned to the frontend."""
    input: str
    claim_verdicts: list[ClaimVerdict]
    model_fast: str = Field(..., description="Fast model ID actually used")
    model_reasoning: str = Field(..., description="Reasoning model ID actually used")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ──────────────────────────────────────────────
# SSE Event Types
# ──────────────────────────────────────────────

class StepEvent(BaseModel):
    """Progress step event sent via SSE."""
    step: str
    message: str


class ClaimsEvent(BaseModel):
    """Partial result: extracted claims."""
    claims: list[ExtractedClaim]


class ErrorEvent(BaseModel):
    """Error event sent via SSE."""
    message: str
    detail: str | None = None
