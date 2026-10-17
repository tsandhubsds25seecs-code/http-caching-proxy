# http-caching-proxy
HTTP/1.1 caching forward proxy built from scratch in Python. Parses HTTP at the socket level, caches responses using RFC 9111 rules, revalidates stale entries with ETag/Last-Modified, and logs hit/miss/revalidation metrics for evaluation.
