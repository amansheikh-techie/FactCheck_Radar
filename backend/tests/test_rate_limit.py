"""Unit tests for IP rate limiting and X-Forwarded-For header extraction."""

import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from backend.app.utils.rate_limit import IPRateLimiter


def test_get_client_ip_with_x_forwarded_for():
    limiter = IPRateLimiter(max_requests=2, window_seconds=60)
    
    # Proxy chain: client, proxy1, proxy2
    mock_request = MagicMock()
    mock_request.headers = {"X-Forwarded-For": "203.0.113.195, 70.41.3.18, 150.172.238.178"}
    
    client_ip = limiter.get_client_ip(mock_request)
    assert client_ip == "203.0.113.195"


def test_get_client_ip_direct():
    limiter = IPRateLimiter(max_requests=2, window_seconds=60)
    
    mock_request = MagicMock()
    mock_request.headers = {}
    mock_request.client.host = "198.51.100.42"
    
    client_ip = limiter.get_client_ip(mock_request)
    assert client_ip == "198.51.100.42"


def test_rate_limiter_enforces_limit():
    limiter = IPRateLimiter(max_requests=3, window_seconds=60)
    
    mock_request = MagicMock()
    mock_request.headers = {"X-Forwarded-For": "198.51.100.99"}
    
    # 3 allowed
    limiter.check(mock_request)
    limiter.check(mock_request)
    limiter.check(mock_request)
    
    # 4th raises 429
    with pytest.raises(HTTPException) as exc_info:
        limiter.check(mock_request)
    
    assert exc_info.value.status_code == 429
    assert "Rate limit exceeded" in exc_info.value.detail
    assert "Retry-After" in exc_info.value.headers
