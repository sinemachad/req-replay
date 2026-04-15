"""Filter and search captured requests by various criteria."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from req_replay.models import CapturedRequest


@dataclass
class FilterCriteria:
    """Criteria used to filter captured requests."""

    method: Optional[str] = None          # e.g. "GET", "POST"
    url_pattern: Optional[str] = None     # regex applied to the URL
    tags: List[str] = field(default_factory=list)  # all tags must be present
    status_code: Optional[int] = None     # filter by response status (unused here)
    host: Optional[str] = None            # substring match on host


def _matches(request: CapturedRequest, criteria: FilterCriteria) -> bool:
    """Return True if *request* satisfies every non-None criterion."""
    if criteria.method and request.method.upper() != criteria.method.upper():
        return False

    if criteria.url_pattern:
        try:
            if not re.search(criteria.url_pattern, request.url):
                return False
        except re.error as exc:
            raise ValueError(f"Invalid url_pattern regex: {exc}") from exc

    if criteria.host:
        if criteria.host.lower() not in request.url.lower():
            return False

    if criteria.tags:
        request_tags = set(request.tags or [])
        if not set(criteria.tags).issubset(request_tags):
            return False

    return True


def filter_requests(
    requests: List[CapturedRequest],
    criteria: FilterCriteria,
) -> List[CapturedRequest]:
    """Return the subset of *requests* that match *criteria*."""
    return [r for r in requests if _matches(r, criteria)]
