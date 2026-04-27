"""Analyse which headers appear across a collection of requests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from req_replay.models import CapturedRequest


@dataclass
class HeaderCoverageStats:
    total_requests: int
    header_presence: Dict[str, int] = field(default_factory=dict)
    header_coverage: Dict[str, float] = field(default_factory=dict)

    def display(self) -> str:  # pragma: no cover
        lines = [f"Total requests: {self.total_requests}"]
        if not self.header_presence:
            lines.append("  No headers found.")
            return "\n".join(lines)
        lines.append(f"  {'Header':<40} {'Count':>6}  {'Coverage':>8}")
        lines.append("  " + "-" * 58)
        for key, count in sorted(
            self.header_presence.items(), key=lambda x: -x[1]
        ):
            pct = self.header_coverage.get(key, 0.0)
            lines.append(f"  {key:<40} {count:>6}  {pct:>7.1f}%")
        return "\n".join(lines)

    def top(self, n: int = 5) -> List[str]:
        """Return the top-n most common header keys."""
        return [
            k
            for k, _ in sorted(
                self.header_presence.items(), key=lambda x: -x[1]
            )[:n]
        ]

    def missing_from(self, request: CapturedRequest) -> List[str]:
        """Return header keys that exist in the corpus but not in *request*."""
        present = {k.lower() for k in request.headers}
        return [k for k in self.header_presence if k not in present]


def analyze_header_coverage(
    requests: Sequence[CapturedRequest],
) -> HeaderCoverageStats:
    """Count how many requests contain each header key."""
    total = len(requests)
    presence: Dict[str, int] = {}

    for req in requests:
        seen: set = set()
        for key in req.headers:
            norm = key.lower()
            if norm not in seen:
                presence[norm] = presence.get(norm, 0) + 1
                seen.add(norm)

    coverage = {
        k: (v / total * 100) if total else 0.0
        for k, v in presence.items()
    }

    return HeaderCoverageStats(
        total_requests=total,
        header_presence=presence,
        header_coverage=coverage,
    )
