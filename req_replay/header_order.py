"""Analyse and compare HTTP header ordering across captured requests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Sequence

from req_replay.models import CapturedRequest


@dataclass
class HeaderOrderResult:
    request_id: str
    ordered_keys: List[str]
    canonical_keys: List[str]  # sorted baseline
    deviations: List[str]  # keys that appear out-of-canonical order

    @property
    def is_canonical(self) -> bool:
        return len(self.deviations) == 0

    def display(self) -> str:
        lines = [
            f"Request : {self.request_id}",
            f"Order   : {', '.join(self.ordered_keys)}",
            f"Canonical: {', '.join(self.canonical_keys)}",
        ]
        if self.is_canonical:
            lines.append("Status  : canonical ✓")
        else:
            lines.append(f"Status  : non-canonical — deviations: {', '.join(self.deviations)}")
        return "\n".join(lines)


@dataclass
class HeaderOrderStats:
    total: int = 0
    canonical_count: int = 0
    non_canonical_count: int = 0
    most_common_order: List[str] = field(default_factory=list)

    def display(self) -> str:
        pct = (self.canonical_count / self.total * 100) if self.total else 0.0
        return (
            f"Total requests  : {self.total}\n"
            f"Canonical order : {self.canonical_count} ({pct:.1f}%)\n"
            f"Non-canonical   : {self.non_canonical_count}\n"
            f"Most common order: {', '.join(self.most_common_order)}"
        )


def analyze_header_order(request: CapturedRequest) -> HeaderOrderResult:
    """Return ordering analysis for a single request."""
    keys = [k.lower() for k in request.headers.keys()]
    canonical = sorted(keys)
    deviations = [k for i, k in enumerate(keys) if k != canonical[i]]
    return HeaderOrderResult(
        request_id=request.id,
        ordered_keys=keys,
        canonical_keys=canonical,
        deviations=deviations,
    )


def summarize_header_orders(requests: Sequence[CapturedRequest]) -> HeaderOrderStats:
    """Aggregate header-order statistics across many requests."""
    if not requests:
        return HeaderOrderStats()

    results = [analyze_header_order(r) for r in requests]
    canonical = sum(1 for r in results if r.is_canonical)

    # find most common ordering by joining keys as a tuple key
    freq: Dict[tuple, int] = {}
    for r in results:
        key = tuple(r.ordered_keys)
        freq[key] = freq.get(key, 0) + 1
    most_common = list(max(freq, key=lambda k: freq[k])) if freq else []

    return HeaderOrderStats(
        total=len(results),
        canonical_count=canonical,
        non_canonical_count=len(results) - canonical,
        most_common_order=most_common,
    )
