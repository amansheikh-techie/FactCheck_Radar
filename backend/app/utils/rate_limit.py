"""In-memory sliding-window IP rate limiter with proxy (X-Forwarded-For) support."""

from __future__ import annotations

import time
from collections import defaultdict
from fastapi import Request, HTTPException


class IPRateLimiter:
    """
    Limits requests per IP address across a sliding time window.
    Extracts client IP from X-Forwarded-For when deployed behind reverse proxies
    (Render, Nebius, Cloudflare, AWS ALB), falling back to direct client host.
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def get_client_ip(self, request: Request) -> str:
        """Extract the true originating client IP address."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # The client IP is the first entry in X-Forwarded-For: client, proxy1, proxy2
            return forwarded.split(",")[0].strip()
        if request.client and request.client.host:
            return request.client.host
        return "127.0.0.1"

    def check(self, request: Request) -> None:
        """
        Record a request from the client IP and enforce the rate limit.
        Raises HTTPException(429) with friendly details and Retry-After header.
        """
        ip = self.get_client_ip(request)
        now = time.time()
        cutoff = now - self.window_seconds

        # Prune old timestamps
        recent = [t for t in self.requests[ip] if t > cutoff]

        if len(recent) >= self.max_requests:
            retry_after = max(1, int(self.window_seconds - (now - recent[0])) + 1)
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Rate limit exceeded: maximum {self.max_requests} requests per minute. "
                    f"Please wait {retry_after} seconds before submitting another check."
                ),
                headers={"Retry-After": str(retry_after)},
            )

        recent.append(now)
        self.requests[ip] = recent


# Singleton instance: 10 requests per minute per IP
rate_limiter = IPRateLimiter(max_requests=10, window_seconds=60)
