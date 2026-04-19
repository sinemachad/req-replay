"""URL pattern matching and frequency analysis for captured requests."""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from req_replay.models import CapturedRequest

# Common path segment patterns
_UUID = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
_INT_ID = re.compile(r'^\ndef _normal(seg: str) -> str:
     _UUID.match(seg):
uuid}'
    if _INT_ID'
    return seg


def normalise_path(path: str) -> str:
    """Replace dynamic segments with placeholders."""
    parts = path.split('/')
    return '/'.join(_normalise_segment(p) for p in parts)


@dataclass
class PatternStats:
    total: int
    patterns: Dict[str, int] = field(default_factory=dict)  # pattern -> count
    top_n: List[tuple] = field(default_factory=list)

    def display(self) -> str:
        lines = [f"Total requests: {self.total}", "Top URL patterns:"]
        for pat, cnt in self.top_n:
            lines.append(f"  {cnt:>5}  {pat}")
        return '\n'.join(lines)


def analyze_patterns(requests: List[CapturedRequest], top: int = 10) -> PatternStats:
    """Analyse URL path patterns across a list of requests."""
    counter: Counter = Counter()
    for req in requests:
        try:
            from urllib.parse import urlparse
            path = urlparse(req.url).path or '/'
        except Exception:
            path = '/'
        pattern = normalise_path(path)
        method = req.method.upper()
        counter[f"{method} {pattern}"] += 1

    top_n = counter.most_common(top)
    return PatternStats(
        total=len(requests),
        patterns=dict(counter),
        top_n=top_n,
    )
