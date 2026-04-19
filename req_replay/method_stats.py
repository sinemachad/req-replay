from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter
from typing import List

from req_replay.models import CapturedRequest


@dataclass
class MethodStats:
    total: int
    counts: dict[str, int]
    percentages: dict[str, float]

    def display(self) -> str:
        lines = [f"Total requests: {self.total}"]
        for method, count in sorted(self.counts.items(), key=lambda x: -x[1]):
            pct = self.percentages.get(method, 0.0)
            lines.append(f"  {method:<10} {count:>5}  ({pct:.1f}%)")
        return "\n".join(lines)

    def top(self, n: int = 3) -> list[tuple[str, int]]:
        return sorted(self.counts.items(), key=lambda x: -x[1])[:n]


def analyze_methods(requests: List[CapturedRequest]) -> MethodStats:
    if not requests:
        return MethodStats(total=0, counts={}, percentages={})

    counts: Counter = Counter()
    for req in requests:
        method = (req.method or "UNKNOWN").upper()
        counts[method] += 1

    total = sum(counts.values())
    percentages = {m: (c / total * 100) for m, c in counts.items()}

    return MethodStats(
        total=total,
        counts=dict(counts),
        percentages=percentages,
    )
