"""URL content extraction using trafilatura."""

from __future__ import annotations

import logging
import re

import httpx
import trafilatura

logger = logging.getLogger(__name__)

# Simple URL pattern
URL_PATTERN = re.compile(
    r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE
)


def is_url(text: str) -> bool:
    """Check if the input looks like a URL."""
    return bool(URL_PATTERN.match(text.strip()))


async def extract_text_from_url(url: str, timeout: float = 15.0) -> str:
    """
    Fetch a URL and extract the main article text using trafilatura.
    Returns the extracted text or raises ValueError on failure.
    """
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "FactCheckRadar/1.0 (research tool)"},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text
    except httpx.HTTPError as exc:
        raise ValueError(f"Failed to fetch URL: {exc}") from exc

    extracted = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        favor_recall=True,
    )

    if not extracted or len(extracted.strip()) < 50:
        raise ValueError(
            f"Could not extract meaningful text from {url}. "
            "The page may be behind a paywall or require JavaScript."
        )

    logger.info("Extracted %d chars from %s", len(extracted), url)
    # Cap at 3000 chars to avoid overwhelming the LLM
    return extracted[:3000]
