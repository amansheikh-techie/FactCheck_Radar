"""Simple in-memory TTL cache with LRU eviction."""

from __future__ import annotations

import hashlib
import time
import logging
from collections import OrderedDict
from typing import Any

from backend.app.config import settings

logger = logging.getLogger(__name__)


class TTLCache:
    """Thread-safe in-memory cache with TTL and max entries."""

    def __init__(
        self,
        ttl_seconds: int | None = None,
        max_entries: int | None = None,
    ) -> None:
        self._ttl = ttl_seconds or settings.cache_ttl_seconds
        self._max = max_entries or settings.max_cache_entries
        self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()

    @staticmethod
    def make_key(text: str) -> str:
        """Create a cache key from normalized input text."""
        normalized = " ".join(text.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def get(self, key: str) -> Any | None:
        """Get a cached value if it exists and hasn't expired."""
        if key not in self._store:
            return None
        value, ts = self._store[key]
        if time.time() - ts > self._ttl:
            del self._store[key]
            return None
        # Move to end (most recently used)
        self._store.move_to_end(key)
        logger.debug("Cache hit for key %s", key)
        return value

    def set(self, key: str, value: Any) -> None:
        """Store a value with the current timestamp."""
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = (value, time.time())
        # Evict oldest if over limit
        while len(self._store) > self._max:
            evicted_key, _ = self._store.popitem(last=False)
            logger.debug("Cache evicted key %s", evicted_key)

    def clear(self) -> None:
        self._store.clear()


# Singleton
cache = TTLCache()
