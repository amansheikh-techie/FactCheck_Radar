"""Retry with exponential backoff utility."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def retry_with_backoff(
    fn: Callable[..., T],
    *args: Any,
    max_retries: int = 2,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    retry_on: tuple[type[Exception], ...] = (Exception,),
    **kwargs: Any,
) -> T:
    """
    Call `fn` with retries and exponential backoff.
    Only retries on exceptions matching `retry_on`.
    """
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            result = fn(*args, **kwargs)
            # If the function is a coroutine, await it
            if asyncio.iscoroutine(result):
                result = await result
            return result
        except retry_on as exc:
            last_exc = exc
            if attempt < max_retries:
                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warning(
                    "Attempt %d/%d failed (%s), retrying in %.1fs...",
                    attempt + 1, max_retries + 1, exc, delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "All %d attempts failed. Last error: %s",
                    max_retries + 1, exc,
                )
    raise last_exc  # type: ignore[misc]
