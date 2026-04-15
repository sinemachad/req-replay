"""Tag management utilities for captured requests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from req_replay.models import CapturedRequest


@dataclass
class TagSummary:
    tag: str
    count: int
    request_ids: list[str] = field(default_factory=list)

    def display(self) -> str:
        return f"{self.tag!r}: {self.count} request(s)"


def add_tags(request: CapturedRequest, tags: Iterable[str]) -> CapturedRequest:
    """Return a new CapturedRequest with the given tags merged in."""
    merged = sorted(set(request.tags) | set(tags))
    return CapturedRequest(
        id=request.id,
        timestamp=request.timestamp,
        method=request.method,
        url=request.url,
        headers=request.headers,
        body=request.body,
        tags=merged,
    )


def remove_tags(request: CapturedRequest, tags: Iterable[str]) -> CapturedRequest:
    """Return a new CapturedRequest with the given tags removed."""
    to_remove = set(tags)
    remaining = [t for t in request.tags if t not in to_remove]
    return CapturedRequest(
        id=request.id,
        timestamp=request.timestamp,
        method=request.method,
        url=request.url,
        headers=request.headers,
        body=request.body,
        tags=remaining,
    )


def summarize_tags(requests: Iterable[CapturedRequest]) -> list[TagSummary]:
    """Aggregate tag usage across a collection of requests."""
    counts: dict[str, list[str]] = {}
    for req in requests:
        for tag in req.tags:
            counts.setdefault(tag, []).append(req.id)
    return [
        TagSummary(tag=tag, count=len(ids), request_ids=ids)
        for tag, ids in sorted(counts.items())
    ]
