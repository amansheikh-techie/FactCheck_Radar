"""Tavily web search service with deduplication and error handling."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import urlparse

from tavily import TavilyClient

from backend.app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result from Tavily."""
    title: str
    url: str
    domain: str
    snippet: str
    score: float


class TavilyService:
    """Wraps the Tavily Python SDK for web evidence retrieval."""

    def __init__(self) -> None:
        if not settings.tavily_api_key:
            logger.warning("TAVILY_API_KEY is not set — web search will fail")
        self._client: TavilyClient | None = None

    def _get_client(self) -> TavilyClient:
        if self._client is None:
            self._client = TavilyClient(api_key=settings.tavily_api_key)
        return self._client

    async def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:
        """Run a Tavily search and return parsed results."""
        try:
            client = self._get_client()
            response = client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced",
            )
            results = []
            for item in response.get("results", []):
                domain = urlparse(item.get("url", "")).netloc
                results.append(SearchResult(
                    title=item.get("title", "Untitled"),
                    url=item.get("url", ""),
                    domain=domain,
                    snippet=item.get("content", "")[:500],
                    score=item.get("score", 0.0),
                ))
            logger.info("Tavily search for '%s' returned %d results", query[:60], len(results))
            return results
        except Exception as exc:
            logger.error("Tavily search failed for '%s': %s", query[:60], exc)
            return []

    async def search_multiple(
        self,
        queries: list[str],
        max_results_per_query: int = 5,
    ) -> list[SearchResult]:
        """
        Run multiple searches and return deduplicated results.
        Deduplicates by domain to avoid one source dominating.
        """
        all_results: list[SearchResult] = []
        seen_domains: set[str] = set()

        for query in queries:
            results = await self.search(query, max_results=max_results_per_query)
            for r in results:
                if r.domain not in seen_domains:
                    seen_domains.add(r.domain)
                    all_results.append(r)
                elif len([x for x in all_results if x.domain == r.domain]) < 2:
                    # Allow up to 2 results from the same domain
                    all_results.append(r)

        return all_results


# Singleton
tavily_service = TavilyService()
