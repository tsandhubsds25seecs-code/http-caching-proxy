# http-caching-proxy
HTTP/1.1 caching forward proxy built from scratch in Python. Parses HTTP at the socket level, caches responses using RFC 9111 rules, revalidates stale entries with ETag/Last-Modified, and logs hit/miss/revalidation metrics for evaluation.
# HTTP Caching Proxy with Request Analysis

A student-written HTTP/1.1 caching forward proxy in Python.

## Team
- Tayyab Ali Sandhu (00000540469) — Cache, freshness, revalidation, logging
- Ahmed Abdullah (00000545320) — Parser, forwarding, concurrency

## What It Does
- Parses HTTP/1.1 at socket level
- Caches responses per RFC 9111
- Revalidates with ETag / Last-Modified
- Logs hit/miss/revalidation metrics

## Status
🚧 In development — Submission 1 scope finalized, implementation starting.

## Report
The Submission 1 report is submitted separately to the instructor and is not stored in this repository.
