"""Latency analysis for captured request/response pairs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from statistics import mean, median, stdev

from req_replay.models import CapturedRequest


@dataclass
class LatencyStats:
    count: int
    min_ms: float
    max_ms: float
    mean_ms: float
    median_ms: float
    p95_ms: float
    stdev_ms: Optional[float]
    samples: List[float] = field(repr=False)

    def display(self) -> str:
        lines = [
            f"Requests : {self.count}",
            f"Min      : {self.min_ms:.1f} ms",
            f"Max      : {self.max_ms:.1f} ms",
            f"Mean     : {self.mean_ms:.1f} ms",
            f"Median   : {self.median_ms:.1f} ms",
            f"p95      : {self.p95_ms:.1f} ms",
        ]
        if self.stdev_ms is not None:
            lines.append(f"Stdev    : {self.stdev_ms:.1f} ms")
        return "\n".join(lines)


def _percentile(sorted_data: List[float], pct: float) -> float:
    if not sorted_data:
        return 0.0
    k = (len(sorted_data) - 1) * pct
    lo, hi = int(k), min(int(k) + 1, len(sorted_data) - 1)
    return sorted_data[lo] + (sorted_data[hi] - sorted_data[lo]) * (k - lo)


def analyze_latency(requests: List[CapturedRequest]) -> Optional[LatencyStats]:
    """Return latency statistics from the duration_ms field of each request."""
    samples = [
        r.metadata["duration_ms"]
        for r in requests
        if isinstance(r.metadata.get("duration_ms"), (int, float))
    ]
    if not samples:
        return None
    s = sorted(samples)
    return LatencyStats(
        count=len(s),
        min_ms=s[0],
        max_ms=s[-1],
        mean_ms=mean(s),
        median_ms=median(s),
        p95_ms=_percentile(s, 0.95),
        stdev_ms=stdev(s) if len(s) > 1 else None,
        samples=s,
    )
