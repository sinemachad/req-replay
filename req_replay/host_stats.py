"""Analyze request distribution by host/domain."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter
from typing import List, Tuple
from urllib.parse import urlparse

from req_replay.models import CapturedRequest


@dataclass
class HostStats:
    total: int
    host_counts: dict[str, int]
    top_hosts: List[Tuple[str, int]]

    def display(self) -> str:
        if self.total == 0:
            return "No requests found."
        lines = [f"Total requests: {self.total}", ""]
        lines.append(f"{'Host':<45} {'Count':>6}  {'%':>6}")
        lines.append("-" * 60)
        for host, count in self.top_hosts:
            pct = 100.0 * count / self.total
            lines.append(f"{host:<45} {count:>6}  {pct:>5.1f}%")
        return "\n".join(lines)


def _extract_host(url: str) -> str:
    try:
        parsed = urlparse(url)
        return parsed.netloc or parsed.path.split("/")[0]
    except Exception:
        return "unknown"


def analyze_hosts(
    requests: List[CapturedRequest],
    top_n: int = 10,
) -> HostStats:
    counter: Counter = Counter()
    for req in requests:
        host = _extract_host(req.url)
        counter[host] += 1
    top = counter.most_common(top_n)
    return HostStats(
        total=len(requests),
        host_counts=dict(counter),
        top_hosts=top,
    )
