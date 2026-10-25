"""Unit tests for the TTL cache with LRU eviction."""

import time
from backend.app.utils.cache import TTLCache


def test_cache_hit_and_miss():
    cache = TTLCache(ttl_seconds=5, max_entries=10)
    key = cache.make_key("The Earth orbits the Sun")
    
    # Initial miss
    assert cache.get(key) is None

    # Set and hit
    cache.set(key, {"verdict": "True"})
    hit = cache.get(key)
    assert hit is not None
    assert hit["verdict"] == "True"


def test_cache_normalization():
    cache = TTLCache()
    # Extra whitespace and different casing should produce identical keys
    k1 = cache.make_key("The Earth   is Round")
    k2 = cache.make_key("the earth is round")
    assert k1 == k2


def test_cache_expiration():
    # Cache with 1 second TTL
    cache = TTLCache(ttl_seconds=1, max_entries=5)
    key = cache.make_key("Temporary data")
    cache.set(key, "data")
    
    assert cache.get(key) == "data"
    time.sleep(1.1)
    # Expired
    assert cache.get(key) is None


def test_cache_lru_eviction():
    # Cache with capacity of 2 items
    cache = TTLCache(ttl_seconds=60, max_entries=2)
    cache.set("a", 1)
    cache.set("b", 2)
    
    # Access 'a' to make it more recently used than 'b'
    _ = cache.get("a")
    
    # Insert 'c' -> should evict 'b' (oldest accessed)
    cache.set("c", 3)
    
    assert cache.get("a") == 1
    assert cache.get("b") is None
    assert cache.get("c") == 3
