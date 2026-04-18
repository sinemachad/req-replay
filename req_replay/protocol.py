"""Detect and summarize HTTP protocol versions used in captured requests."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Tuple

from req_replay.models import CapturedRequest


@dataclass
class ProtocolStats:
    total: int
    version_counts: dict[str, int]
    most_common: str | None

    def display(self) -> str:
        if self.total == 0:
            return "No requests analysed."
        lines = [f"Protocol versions ({self.total} requests):"]
        for version, count in sorted(self.version_counts.items()):
            pct = 100 * count / self.total
            lines.append(f"  {version:<10} {count:>5}  ({pct:.1f}%)")
        lines.append(f"  Most common: {self.most_common}")
        return "\n".join(lines)


def _extract_protocol(req: CapturedRequest) -> str:
    """Return the HTTP protocol version string from request metadata."""
    meta = req.metadata or {}
    raw = meta.get("http_version") or meta.get("protocol") or ""
    if not raw:
        # Infer from URL scheme
        if req.url.startswith("https"):
            return "HTTP/1.1"
        return "HTTP/1.1"
    return str(raw).upper()


def analyze_protocols(requests: List[CapturedRequest]) -> ProtocolStats:
    if not requests:
        return ProtocolStats(total=0, version_counts={}, most_common=None)

    counter: Counter[str] = Counter()
    for req in requests:
        counter[_extract_protocol(req)] += 1

    most_common = counter.most_common(1)[0][0]
    return ProtocolStats(
        total=len(requests),
        version_counts=dict(counter),
        most_common=most_common,
    )
