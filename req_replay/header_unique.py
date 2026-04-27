"""Detect headers that appear in only one request across a collection."""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter
from typing import List, Dict, Set

from req_replay.models import CapturedRequest


@dataclass
class UniqueHeaderResult:
    request_id: str
    unique_headers: List[str]  # header keys present only in this request

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "unique_headers": self.unique_headers,
        }


@dataclass
class UniqueHeaderStats:
    total_requests: int
    total_unique_headers: int
    results: List[UniqueHeaderResult] = field(default_factory=list)

    def display(self) -> str:
        lines = [
            f"Requests analysed : {self.total_requests}",
            f"Requests with unique headers: {len(self.results)}",
            f"Total unique header keys : {self.total_unique_headers}",
        ]
        for r in self.results:
            lines.append(f"  [{r.request_id}] {', '.join(r.unique_headers)}")
        return "\n".join(lines)


def _normalise_key(key: str) -> str:
    return key.strip().lower()


def analyze_unique_headers(
    requests: List[CapturedRequest],
) -> UniqueHeaderStats:
    """Find header keys that appear in exactly one request."""
    if not requests:
        return UniqueHeaderStats(
            total_requests=0,
            total_unique_headers=0,
            results=[],
        )

    # Count how many requests each header key appears in
    key_counter: Counter = Counter()
    per_request: Dict[str, Set[str]] = {}

    for req in requests:
        keys: Set[str] = {
            _normalise_key(k) for k in (req.headers or {}).keys()
        }
        per_request[req.id] = keys
        for k in keys:
            key_counter[k] += 1

    singleton_keys: Set[str] = {
        k for k, count in key_counter.items() if count == 1
    }

    results: List[UniqueHeaderResult] = []
    for req in requests:
        unique = sorted(per_request[req.id] & singleton_keys)
        if unique:
            results.append(UniqueHeaderResult(request_id=req.id, unique_headers=unique))

    return UniqueHeaderStats(
        total_requests=len(requests),
        total_unique_headers=len(singleton_keys),
        results=results,
    )
