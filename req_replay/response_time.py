"""Response time analysis: bucket requests by latency ranges."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from req_replay.models import CapturedRequest

# Buckets: (label, min_ms inclusive, max_ms exclusive)
_DEFAULT_BUCKETS: List[Tuple[str, int, Optional[int]]] = [
    ("<100ms", 0, 100),
    ("100-300ms", 100, 300),
    ("300-500ms", 300, 500),
    ("500ms-1s", 500, 1000),
    (">1s", 1000, None),
]


@dataclass
class ResponseTimeBucket:
    label: str
    min_ms: int
    max_ms: Optional[int]
    count: int = 0
    request_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
            "count": self.count,
            "request_ids": self.request_ids,
        }


@dataclass
class ResponseTimeReport:
    buckets: List[ResponseTimeBucket]
    total: int
    skipped: int  # requests with no duration metadata

    def display(self) -> str:
        lines = [f"Response Time Distribution ({self.total} requests, {self.skipped} skipped)"]
        for b in self.buckets:
            bar = "#" * min(b.count, 40)
            lines.append(f"  {b.label:<14} {b.count:>4}  {bar}")
        return "\n".join(lines)


def _duration_ms(req: CapturedRequest) -> Optional[float]:
    meta = req.metadata or {}
    val = meta.get("duration_ms") or meta.get("elapsed_ms")
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def analyze_response_times(
    requests: List[CapturedRequest],
    buckets: Optional[List[Tuple[str, int, Optional[int]]]] = None,
) -> ResponseTimeReport:
    bucket_defs = buckets or _DEFAULT_BUCKETS
    result_buckets = [
        ResponseTimeBucket(label=lbl, min_ms=lo, max_ms=hi)
        for lbl, lo, hi in bucket_defs
    ]
    total = 0
    skipped = 0
    for req in requests:
        dur = _duration_ms(req)
        if dur is None:
            skipped += 1
            continue
        total += 1
        for b in result_buckets:
            if dur >= b.min_ms and (b.max_ms is None or dur < b.max_ms):
                b.count += 1
                b.request_ids.append(req.id)
                break
    return ResponseTimeReport(buckets=result_buckets, total=total, skipped=skipped)
