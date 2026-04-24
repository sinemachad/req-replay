"""Analyse header usage across captured requests."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Dict

from req_replay.models import CapturedRequest


@dataclass
class HeaderStats:
    total_requests: int
    header_frequency: Dict[str, int] = field(default_factory=dict)
    value_frequency: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def display(self) -> str:
        lines = [f"Total requests analysed: {self.total_requests}", ""]
        lines.append(f"{'Header':<40} {'Count':>6}  {'Coverage':>8}")
        lines.append("-" * 58)
        for name, count in sorted(self.header_frequency.items(), key=lambda x: -x[1]):
            pct = count / self.total_requests * 100 if self.total_requests else 0
            lines.append(f"{name:<40} {count:>6}  {pct:>7.1f}%")
        return "\n".join(lines)

    def top_values(self, header: str, n: int = 5) -> List[tuple[str, int]]:
        """Return the *n* most common values for *header*.

        Args:
            header: Header name (case-insensitive).
            n: Maximum number of entries to return.

        Returns:
            A list of ``(value, count)`` tuples ordered by frequency descending.
            Returns an empty list if the header was not observed.
        """
        counts = self.value_frequency.get(header.lower(), {})
        return sorted(counts.items(), key=lambda x: -x[1])[:n]


def analyze_headers(requests: List[CapturedRequest]) -> HeaderStats:
    """Return frequency statistics for headers across *requests*."""
    header_counter: Counter = Counter()
    value_counters: Dict[str, Counter] = {}

    for req in requests:
        for raw_key, val in req.headers.items():
            key = raw_key.lower()
            header_counter[key] += 1
            value_counters.setdefault(key, Counter())[val] += 1

    return HeaderStats(
        total_requests=len(requests),
        header_frequency=dict(header_counter),
        value_frequency={k: dict(v) for k, v in value_counters.items()},
    )
