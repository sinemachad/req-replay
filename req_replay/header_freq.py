"""Header frequency analysis — counts how often each header appears across requests."""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter
from typing import List, Dict, Tuple

from req_replay.models import CapturedRequest


@dataclass
class HeaderFreqStats:
    total_requests: int
    header_counts: Dict[str, int] = field(default_factory=dict)
    value_counts: Dict[str, Counter] = field(default_factory=dict)

    def top_headers(self, n: int = 10) -> List[Tuple[str, int]]:
        """Return the n most common header names."""
        return sorted(self.header_counts.items(), key=lambda x: x[1], reverse=True)[:n]

    def top_values(self, header: str, n: int = 5) -> List[Tuple[str, int]]:
        """Return the n most common values for a given header."""
        counter = self.value_counts.get(header.lower(), Counter())
        return counter.most_common(n)

    def coverage(self, header: str) -> float:
        """Return fraction of requests that include this header (0.0–1.0)."""
        if self.total_requests == 0:
            return 0.0
        return self.header_counts.get(header.lower(), 0) / self.total_requests

    def display(self) -> str:
        lines = [f"Header Frequency ({self.total_requests} requests)"]
        for name, count in self.top_headers():
            pct = 100.0 * count / self.total_requests if self.total_requests else 0.0
            lines.append(f"  {name}: {count} ({pct:.1f}%)")
        return "\n".join(lines)


def analyze_header_freq(requests: List[CapturedRequest]) -> HeaderFreqStats:
    """Analyse header name/value frequency across all captured requests."""
    header_counts: Dict[str, int] = {}
    value_counts: Dict[str, Counter] = {}

    for req in requests:
        seen: set = set()
        for key, val in (req.headers or {}).items():
            norm = key.lower()
            if norm not in seen:
                header_counts[norm] = header_counts.get(norm, 0) + 1
                seen.add(norm)
            if norm not in value_counts:
                value_counts[norm] = Counter()
            value_counts[norm][val] += 1

    return HeaderFreqStats(
        total_requests=len(requests),
        header_counts=header_counts,
        value_counts=value_counts,
    )
