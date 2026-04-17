"""Rate analysis: compute request rates over a time window."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict

from req_replay.models import CapturedRequest


@dataclass
class RateWindow:
    start: datetime
    end: datetime
    count: int
    methods: Dict[str, int] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        return max((self.end - self.start).total_seconds(), 1.0)

    @property
    def requests_per_second(self) -> float:
        return self.count / self.duration_seconds

    @property
    def requests_per_minute(self) -> float:
        return self.requests_per_second * 60

    def summary(self) -> str:
        return (
            f"Window {self.start.isoformat()} -> {self.end.isoformat()} | "
            f"count={self.count} | "
            f"rps={self.requests_per_second:.2f} | "
            f"rpm={self.requests_per_minute:.2f}"
        )


def analyze_rate(
    requests: List[CapturedRequest],
    window_seconds: int = 60,
) -> List[RateWindow]:
    """Bucket requests into fixed-width time windows and compute rates."""
    if not requests:
        return []

    sorted_reqs = sorted(requests, key=lambda r: r.timestamp)
    window_delta = timedelta(seconds=window_seconds)

    windows: List[RateWindow] = []
    window_start = sorted_reqs[0].timestamp
    window_end = window_start + window_delta
    bucket: List[CapturedRequest] = []

    for req in sorted_reqs:
        while req.timestamp >= window_end:
            if bucket:
                windows.append(_make_window(bucket, window_start, window_end))
            window_start = window_end
            window_end = window_start + window_delta
            bucket = []
        bucket.append(req)

    if bucket:
        windows.append(_make_window(bucket, window_start, window_end))

    return windows


def _make_window(
    reqs: List[CapturedRequest],
    start: datetime,
    end: datetime,
) -> RateWindow:
    methods: Dict[str, int] = {}
    for r in reqs:
        methods[r.method.upper()] = methods.get(r.method.upper(), 0) + 1
    return RateWindow(start=start, end=end, count=len(reqs), methods=methods)
