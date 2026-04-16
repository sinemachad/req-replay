"""Deduplication utilities for captured requests."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import List, Tuple

from .models import CapturedRequest


def _request_fingerprint(req: CapturedRequest) -> str:
    """Return a stable hash that identifies a request by its content."""
    canonical = {
        "method": req.method.upper(),
        "url": req.url,
        "headers": sorted((k.lower(), v) for k, v in req.headers.items()),
        "body": req.body,
    }
    raw = json.dumps(canonical, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


@dataclass
class DedupeResult:
    unique: List[CapturedRequest]
    duplicates: List[Tuple[CapturedRequest, CapturedRequest]]  # (kept, duplicate)

    @property
    def duplicate_count(self) -> int:
        return len(self.duplicates)

    def summary(self) -> str:
        return (
            f"{len(self.unique)} unique request(s), "
            f"{self.duplicate_count} duplicate(s) removed."
        )


def deduplicate(requests: List[CapturedRequest]) -> DedupeResult:
    """Return unique requests, preserving first occurrence order.

    Two requests are considered duplicates when they share the same
    method, URL, headers (case-insensitive keys) and body.
    """
    seen: dict[str, CapturedRequest] = {}
    unique: List[CapturedRequest] = []
    duplicates: List[Tuple[CapturedRequest, CapturedRequest]] = []

    for req in requests:
        fp = _request_fingerprint(req)
        if fp in seen:
            duplicates.append((seen[fp], req))
        else:
            seen[fp] = req
            unique.append(req)

    return DedupeResult(unique=unique, duplicates=duplicates)
