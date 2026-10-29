"""Fact-check API router with SSE streaming."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from backend.app.schemas import FactCheckRequest, FactCheckResult
from backend.app.agents.pipeline import run_factcheck_pipeline, run_demo_pipeline
from backend.app.utils.cache import cache
from backend.app.utils.rate_limit import rate_limiter
from backend.app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["factcheck"])


@router.post("/factcheck")
async def factcheck(payload: FactCheckRequest, request: Request):
    """
    Run the fact-check pipeline on the given input.
    Returns a Server-Sent Events stream with progress updates and the final result.
    Enforces per-IP rate limiting and input length constraints.
    """
    # Enforce rate limit (10 req/min per IP, proxy-aware)
    rate_limiter.check(request)

    # Validate input length
    if len(payload.input) > settings.max_input_length:
        raise HTTPException(
            status_code=400,
            detail=f"Input too long. Maximum {settings.max_input_length} characters.",
        )

    if not payload.input.strip():
        raise HTTPException(status_code=400, detail="Input cannot be empty.")

    # Explicit demo mode: sample data only appears when user explicitly enables demo mode
    is_demo = payload.demo_mode or settings.demo_mode
    if is_demo:
        logger.info("Explicit demo mode requested by user; running demo pipeline")

    # Check cache (differentiate demo results from live results in key)
    cache_key = cache.make_key(f"{payload.input}:demo={is_demo}")
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

    # Run pipeline with SSE streaming (NO silent fallback to sample data)
    async def event_stream():
        final_result = None

        if is_demo:
            yield f"event: step\ndata: {json.dumps({'step': 'notice', 'message': 'Demo mode enabled — sample result'})}\n\n"
            async for event_line in run_demo_pipeline(payload.input):
                yield event_line
                if "event: result" in event_line:
                    try:
                        data_line = event_line.split("data: ", 1)[1].strip()
                        final_result = json.loads(data_line)
                    except (IndexError, json.JSONDecodeError):
                        pass
        else:
            # Live pipeline strictly: fails on any API error without falling back to sample data
            try:
                async for event_line in run_factcheck_pipeline(payload.input):
                    yield event_line
                    if "event: result" in event_line:
                        try:
                            data_line = event_line.split("data: ", 1)[1].strip()
                            final_result = json.loads(data_line)
                        except (IndexError, json.JSONDecodeError):
                            pass
            except Exception as exc:
                logger.error("Live pipeline error: %s", exc)
                yield f"event: error\ndata: {json.dumps({'message': f'Live API error: {str(exc)}'})}\n\n"

        # Cache the result if successfully generated
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
