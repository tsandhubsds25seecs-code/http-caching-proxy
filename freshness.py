"""
RFC 9111 freshness and age computation.
Owner: Tayyab Ali Sandhu (00000540469)
"""

"""
RFC 9111 freshness and age computation.
"""
from email.utils import parsedate_to_datetime
import time


def parse_date_header(value):
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).timestamp()
    except (TypeError, ValueError):
        return None


def compute_freshness_lifetime(headers):
    """
    Compute freshness lifetime (seconds).
    Returns None if response is not cacheable.
    """
    header_map = {k.lower(): v for k, v in headers}

    cc = header_map.get("cache-control", "").lower()
    if "no-store" in cc:
        return None
    if "no-cache" in cc:
        return 0

    for directive in cc.split(","):
        directive = directive.strip()
        if directive.startswith("max-age="):
            try:
                return int(directive.split("=")[1])
            except ValueError:
                return None

    expires = parse_date_header(header_map.get("expires"))
    date_val = parse_date_header(header_map.get("date"))
    if expires is not None and date_val is not None:
        return max(0, int(expires - date_val))

    return None  # no freshness info — do not cache


def compute_current_age(headers, response_time):
    """Compute current age in seconds (simplified RFC 9111)."""
    header_map = {k.lower(): v for k, v in headers}
    date_val = parse_date_header(header_map.get("date"))
    try:
        age_val = int(header_map.get("age", "0") or 0)
    except ValueError:
        age_val = 0

    if date_val is None:
        return age_val

    apparent_age = max(0, response_time - date_val)
    corrected_age = age_val
    initial_age = max(apparent_age, corrected_age)
    return initial_age