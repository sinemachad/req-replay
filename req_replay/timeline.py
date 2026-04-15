"""Timeline: group and summarise captured requests by time bucket."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from req_replay.models import CapturedRequest


@dataclass
class TimelineBucket:
    """A single time bucket containing one or more captured requests."""

    label: str  # e.g. "2024-01-15 14:05"
    requests: List[CapturedRequest] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.requests)

    @property
    def methods(self) -> Dict[str, int]:
        """Count of each HTTP method in this bucket."""
        counts: Dict[str, int] = {}
        for req in self.requests:
            counts[req.method] = counts.get(req.method, 0) + 1
        return counts

    def summary(self) -> str:
        method_str = ", ".join(f"{m}:{c}" for m, c in sorted(self.methods.items()))
        return f"[{self.label}] {self.count} request(s) — {method_str}"


def _bucket_label(ts: datetime, granularity: str) -> str:
    """Return a string label for *ts* at the requested granularity.

    Supported granularities: 'minute', 'hour', 'day'.
    """
    if granularity == "minute":
        return ts.strftime("%Y-%m-%d %H:%M")
    if granularity == "hour":
        return ts.strftime("%Y-%m-%d %H:00")
    if granularity == "day":
        return ts.strftime("%Y-%m-%d")
    raise ValueError(f"Unknown granularity: {granularity!r}. Use 'minute', 'hour', or 'day'.")


def build_timeline(
    requests: List[CapturedRequest],
    granularity: str = "minute",
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[TimelineBucket]:
    """Group *requests* into :class:`TimelineBucket` objects.

    Parameters
    ----------
    requests:
        Flat list of captured requests to group.
    granularity:
        Time bucket size — ``'minute'``, ``'hour'``, or ``'day'``.
    start / end:
        Optional inclusive datetime bounds for filtering.
    """
    buckets: Dict[str, TimelineBucket] = {}

    for req in requests:
        ts = req.timestamp
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        if start and ts < start:
            continue
        if end and ts > end:
            continue

        label = _bucket_label(ts, granularity)
        if label not in buckets:
            buckets[label] = TimelineBucket(label=label)
        buckets[label].requests.append(req)

    return [buckets[k] for k in sorted(buckets)]
