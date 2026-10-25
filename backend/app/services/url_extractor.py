"""URL content extraction using trafilatura."""

from __future__ import annotations

import ipaddress
import logging
import re
from urllib.parse import urlparse

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


def is_safe_url(url: str) -> bool:
    """Validate that the URL does not point to internal/private infrastructure (SSRF protection)."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = (parsed.hostname or "").lower()
        if not hostname or hostname in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            return False

        # If hostname is an IP, check if private, loopback, or link-local
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
        except ValueError:
            # Valid domain name
            pass

        return True
    except Exception:
        return False


async def extract_text_from_url(url: str, timeout: float = 15.0) -> str:
    """
    Fetch a URL and extract the main article text using trafilatura.
    Returns the extracted text or raises ValueError on failure.
    """
    if not is_safe_url(url):
        raise ValueError(f"Invalid or disallowed URL target: {url}")

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
