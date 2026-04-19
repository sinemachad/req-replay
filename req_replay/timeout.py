"""Timeout analysis for captured request/response pairs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from req_replay.models import CapturedRequest, CapturedResponse


@dataclass
class TimeoutStats:
    total: int
    timed_out: int
    timeout_rate: float  # 0.0 – 1.0
    threshold_ms: float
    slowest_ms: Optional[float]
    slowest_url: Optional[str]

    def display(self) -> str:
        lines = [
            f"Threshold : {self.threshold_ms} ms",
            f"Total     : {self.total}",
            f"Timed out : {self.timed_out} ({self.timeout_rate * 100:.1f}%)",
        ]
        if self.slowest_url is not None:
            lines.append(f"Slowest   : {self.slowest_ms:.1f} ms  {self.slowest_url}")
        return "\n".join(lines)


def _duration_ms(req: CapturedRequest) -> Optional[float]:
    """Return duration_ms from request metadata if present."""
    meta = req.metadata or {}
    val = meta.get("duration_ms")
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def analyze_timeouts(
    pairs: List[Tuple[CapturedRequest, CapturedResponse]],
    threshold_ms: float = 5000.0,
) -> TimeoutStats:
    """Analyse pairs and report how many exceeded *threshold_ms*."""
    total = len(pairs)
    timed_out = 0
    slowest_ms: Optional[float] = None
    slowest_url: Optional[str] = None

    for req, _resp in pairs:
        dur = _duration_ms(req)
        if dur is None:
            continue
        if dur > threshold_ms:
            timed_out += 1
        if slowest_ms is None or dur > slowest_ms:
            slowest_ms = dur
            slowest_url = req.url

    rate = (timed_out / total) if total else 0.0
    return TimeoutStats(
        total=total,
        timed_out=timed_out,
        timeout_rate=rate,
        threshold_ms=threshold_ms,
        slowest_ms=slowest_ms,
        slowest_url=slowest_url,
    )
