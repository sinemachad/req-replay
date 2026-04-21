"""Analyze header count statistics across captured requests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from req_replay.models import CapturedRequest


@dataclass
class HeaderCountStats:
    total_requests: int
    min_headers: Optional[int]
    max_headers: Optional[int]
    avg_headers: float
    over_threshold: int  # requests exceeding the given threshold
    distribution: dict = field(default_factory=dict)  # bucket -> count

    def display(self) -> str:
        if self.total_requests == 0:
            return "No requests to analyze."
        lines = [
            f"Total requests : {self.total_requests}",
            f"Min headers    : {self.min_headers}",
            f"Max headers    : {self.max_headers}",
            f"Avg headers    : {self.avg_headers:.1f}",
            f"Over threshold : {self.over_threshold}",
        ]
        if self.distribution:
            lines.append("Distribution:")
            for bucket in sorted(self.distribution):
                lines.append(f"  {bucket:>3} headers: {self.distribution[bucket]}")
        return "\n".join(lines)


def _count_headers(request: CapturedRequest) -> int:
    """Return the number of headers on a request (case-insensitive dedup)."""
    return len(request.headers)


def analyze_header_counts(
    requests: List[CapturedRequest],
    threshold: int = 20,
) -> HeaderCountStats:
    """Compute header count statistics over a list of requests."""
    if not requests:
        return HeaderCountStats(
            total_requests=0,
            min_headers=None,
            max_headers=None,
            avg_headers=0.0,
            over_threshold=0,
        )

    counts = [_count_headers(r) for r in requests]
    distribution: dict = {}
    for c in counts:
        distribution[c] = distribution.get(c, 0) + 1

    return HeaderCountStats(
        total_requests=len(requests),
        min_headers=min(counts),
        max_headers=max(counts),
        avg_headers=sum(counts) / len(counts),
        over_threshold=sum(1 for c in counts if c > threshold),
        distribution=distribution,
    )
