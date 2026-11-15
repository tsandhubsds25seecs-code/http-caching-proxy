"""
Cache store with TTL and LRU eviction.
Owner: Tayyab Ali Sandhu (00000540469)
"""

"""
Thread-safe cache store with TTL and LRU eviction.
"""
import threading
import time
from freshness import compute_current_age


class CacheEntry:
    def __init__(self, status, reason, version, headers, body,
                 date_value, age_value, freshness_lifetime,
                 etag=None, last_modified=None):
        self.status = status
        self.reason = reason
        self.version = version
        self.headers = headers
        self.body = body
        self.date_value = date_value
        self.age_value = age_value
        self.freshness_lifetime = freshness_lifetime
        self.etag = etag
        self.last_modified = last_modified
        self.response_time = time.time()
        self.last_used = time.time()

    def current_age(self):
        base = compute_current_age(self.headers, self.response_time)
        return base + (time.time() - self.response_time)

    def is_fresh(self):
        return self.current_age() < self.freshness_lifetime

    def validators(self):
        h = {}
        if self.etag:
            h["If-None-Match"] = self.etag
        if self.last_modified:
            h["If-Modified-Since"] = self.last_modified
        return h

    def refresh_metadata(self, new_headers):
        """Called on 304 Not Modified."""
        self.headers = new_headers
        self.response_time = time.time()
        self.age_value = 0
        self.last_used = time.time()


class CacheStore:
    def __init__(self, max_entries=1000):
        self._lock = threading.Lock()
        self._store = {}
        self._max = max_entries

    def get(self, key):
        with self._lock:
            entry = self._store.get(key)
            if entry:
                entry.last_used = time.time()
            return entry

    def put(self, key, entry):
        with self._lock:
            if len(self._store) >= self._max:
                oldest_key = min(self._store, key=lambda k: self._store[k].last_used)
                del self._store[oldest_key]
            self._store[key] = entry

    def delete(self, key):
        with self._lock:
            self._store.pop(key, None)

    def size(self):
        with self._lock:
            return len(self._store)

    def clear(self):
        with self._lock:
            self._store.clear()