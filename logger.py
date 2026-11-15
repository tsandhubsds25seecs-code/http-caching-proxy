"""
Per-request logging and aggregate metrics.
Owner: Tayyab Ali Sandhu (00000540469)
"""

"""
Per-request logging and aggregate metrics.
"""
import csv
import threading
import time


class ProxyLogger:
    def __init__(self, log_path="proxy.log"):
        self._lock = threading.Lock()
        self._path = log_path
        self._hits = 0
        self._misses = 0
        self._revalidated = 0
        self._bypass = 0
        self._upstream_bytes = 0
        self._total_ms = 0.0
        self._count = 0

    def log(self, client, method, uri, cache_status, response_ms,
            upstream_bytes, status_code):
        with self._lock:
            if cache_status == "HIT":
                self._hits += 1
            elif cache_status == "MISS":
                self._misses += 1
            elif cache_status.startswith("REVALIDATED"):
                self._revalidated += 1
            elif cache_status == "BYPASS":
                self._bypass += 1

            self._upstream_bytes += upstream_bytes
            self._total_ms += response_ms
            self._count += 1

            with open(self._path, "a", newline="") as f:
                w = csv.writer(f)
                w.writerow([
                    time.strftime("%Y-%m-%dT%H:%M:%S"),
                    client, method, uri, cache_status,
                    f"{response_ms:.1f}", upstream_bytes, status_code,
                ])

    def summary(self):
        with self._lock:
            total = self._hits + self._misses + self._revalidated + self._bypass
            return {
                "total_requests": total,
                "hits": self._hits,
                "misses": self._misses,
                "revalidated": self._revalidated,
                "bypass": self._bypass,
                "hit_ratio": round(self._hits / total, 3) if total else 0.0,
                "mean_response_ms": round(self._total_ms / self._count, 2) if self._count else 0.0,
                "total_upstream_bytes": self._upstream_bytes,
            }