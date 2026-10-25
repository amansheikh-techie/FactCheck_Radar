"""Fact-check API router with SSE streaming."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.app.schemas import FactCheckRequest, FactCheckResult
from backend.app.agents.pipeline import run_factcheck_pipeline
from backend.app.utils.cache import cache
from backend.app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["factcheck"])


@router.post("/factcheck")
async def factcheck(request: FactCheckRequest):
    """
    Run the fact-check pipeline on the given input.
    Returns a Server-Sent Events stream with progress updates and the final result.
    """
    # Validate input length
    if len(request.input) > settings.max_input_length:
        raise HTTPException(
            status_code=400,
            detail=f"Input too long. Maximum {settings.max_input_length} characters.",
        )

    if not request.input.strip():
        raise HTTPException(status_code=400, detail="Input cannot be empty.")

    # Check API keys
    if not settings.nebius_api_key:
        raise HTTPException(
            status_code=503,
            detail="NEBIUS_API_KEY is not configured. Please set it in your .env file.",
        )
    if not settings.tavily_api_key:
        raise HTTPException(
            status_code=503,
            detail="TAVILY_API_KEY is not configured. Please set it in your .env file.",
        )

    # Check cache
    cache_key = cache.make_key(request.input)
    cached_result = cache.get(cache_key)

    if cached_result is not None:
        logger.info("Returning cached result for key %s", cache_key)

        async def cached_stream():
            yield f"event: step\ndata: {json.dumps({'step': 'cached', 'message': 'Returning cached result...'})}\n\n"
            yield f"event: result\ndata: {json.dumps(cached_result)}\n\n"

        return StreamingResponse(
            cached_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Run pipeline with SSE streaming
    async def event_stream():
        final_result = None
        async for event_line in run_factcheck_pipeline(request.input):
            yield event_line
            # Capture the result for caching
            if "event: result" in event_line:
                try:
                    data_line = event_line.split("data: ", 1)[1].strip()
                    final_result = json.loads(data_line)
                except (IndexError, json.JSONDecodeError):
                    pass

        # Cache the result
        if final_result is not None:
            cache.set(cache_key, final_result)
            logger.info("Cached result for key %s", cache_key)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
