"""
Conditional revalidation with ETag and Last-Modified.
Owner: Tayyab Ali Sandhu (00000540469)
"""

"""
Conditional revalidation helpers.
"""


def build_conditional_headers(entry):
    """Build If-None-Match / If-Modified-Since headers."""
    headers = []
    if entry.etag:
        headers.append(("If-None-Match", entry.etag))
    if entry.last_modified:
        headers.append(("If-Modified-Since", entry.last_modified))
    return headers


def is_304(response):
    return response.status == 304