"""Unit tests — run with: python tests/test_all.py"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cache import CacheEntry, CacheStore
from freshness import compute_freshness_lifetime, parse_date_header


def test_freshness():
    headers = [("Cache-Control", "max-age=60"),
               ("Date", "Mon, 01 Jan 2026 00:00:00 GMT")]
    assert compute_freshness_lifetime(headers) == 60
    headers2 = [("Cache-Control", "no-store")]
    assert compute_freshness_lifetime(headers2) is None
    print("PASS: freshness")


def test_cache():
    e = CacheEntry(200, "OK", "HTTP/1.1", [], b"x",
                   time.time(), 0, 60, etag='"v1"')
    assert e.is_fresh()
    assert e.validators() == {"If-None-Match": '"v1"'}
    store = CacheStore()
    store.put("GET:/a", e)
    assert store.get("GET:/a") is e
    print("PASS: cache")


if __name__ == "__main__":
    test_freshness()
    test_cache()
    print("All tests passed.")