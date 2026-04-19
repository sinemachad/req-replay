"""Entropy analysis: detect high-entropy values in request headers/params (potential secrets)."""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Sequence, Tuple
from urllib.parse import urlparse, parse_qs

from req_replay.models import CapturedRequest

DEFAULT_THRESHOLD = 4.5


@dataclass
class EntropyHit:
    location: str  # e.g. "header:Authorization", "query:token"
    value: str
    entropy: float

    def to_dict(self) -> dict:
        return {"location": self.location, "value": self.value[:6] + "...", "entropy": round(self.entropy, 3)}


@dataclass
class EntropyResult:
    hits: List[EntropyHit] = field(default_factory=list)

    def passed(self) -> bool:
        return len(self.hits) == 0

    def summary(self) -> str:
        if self.passed():
            return "No high-entropy values detected."
        lines = [f"  [{h.location}] entropy={h.entropy:.2f}" for h in self.hits]
        return "High-entropy values detected:\n" + "\n".join(lines)

    def display(self) -> None:
        print(self.summary())


def _shannon(value: str) -> float:
    if not value:
        return 0.0
    freq = {c: value.count(c) / len(value) for c in set(value)}
    return -sum(p * math.log2(p) for p in freq.values())


def _check_pairs(pairs: Sequence[Tuple[str, str]], prefix: str, threshold: float) -> List[EntropyHit]:
    hits = []
    for k, v in pairs:
        e = _shannon(v)
        if e >= threshold:
            hits.append(EntropyHit(location=f"{prefix}:{k}", value=v, entropy=e))
    return hits


def analyze_entropy(request: CapturedRequest, threshold: float = DEFAULT_THRESHOLD) -> EntropyResult:
    hits: List[EntropyHit] = []
    hits.extend(_check_pairs(list(request.headers.items()), "header", threshold))
    qs = parse_qs(urlparse(request.url).query)
    for k, vals in qs.items():
        for v in vals:
            e = _shannon(v)
            if e >= threshold:
                hits.append(EntropyHit(location=f"query:{k}", value=v, entropy=e))
    return EntropyResult(hits=hits)
