"""Analyse Time-To-Live (TTL) hints embedded in response headers.

Checks Cache-Control max-age, Expires, and CDN-specific headers to
produce a per-response TTL summary and a cross-request aggregate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from req_replay.models import CapturedRequest, CapturedResponse


@dataclass
class TTLResult:
    request_id: str
    url: str
    ttl_seconds: Optional[int]  # None means no TTL hint found
    source: Optional[str]  # which header provided the value

    def display(self) -> str:
        if self.ttl_seconds is None:
            return f"{self.request_id}  {self.url}  ttl=none"
        return f"{self.request_id}  {self.url}  ttl={self.ttl_seconds}s  (via {self.source})"


@dataclass
class TTLStats:
    results: List[TTLResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def with_ttl(self) -> int:
        return sum(1 for r in self.results if r.ttl_seconds is not None)

    @property
    def without_ttl(self) -> int:
        return self.total - self.with_ttl

    @property
    def average_ttl(self) -> Optional[float]:
        vals = [r.ttl_seconds for r in self.results if r.ttl_seconds is not None]
        return sum(vals) / len(vals) if vals else None

    def display(self) -> str:
        lines = [
            f"Total responses : {self.total}",
            f"With TTL hint   : {self.with_ttl}",
            f"Without TTL hint: {self.without_ttl}",
        ]
        if self.average_ttl is not None:
            lines.append(f"Average TTL     : {self.average_ttl:.1f}s")
        return "\n".join(lines)


def _parse_max_age(cache_control: str) -> Optional[int]:
    for part in cache_control.split(","):
        part = part.strip().lower()
        if part.startswith("max-age="):
            try:
                return int(part.split("=", 1)[1].strip())
            except ValueError:
                return None
    return None


def _header(resp: CapturedResponse, name: str) -> Optional[str]:
    for k, v in resp.headers.items():
        if k.lower() == name.lower():
            return v
    return None


def extract_ttl(resp: CapturedResponse) -> Tuple[Optional[int], Optional[str]]:
    """Return (ttl_seconds, source_header) for *resp*, or (None, None)."""
    cc = _header(resp, "cache-control")
    if cc:
        age = _parse_max_age(cc)
        if age is not None:
            return age, "cache-control"

    cdn_age = _header(resp, "cdn-cache-control")
    if cdn_age:
        age = _parse_max_age(cdn_age)
        if age is not None:
            return age, "cdn-cache-control"

    return None, None


def analyze_ttl(
    pairs: List[Tuple[CapturedRequest, CapturedResponse]],
) -> TTLStats:
    results: List[TTLResult] = []
    for req, resp in pairs:
        ttl, source = extract_ttl(resp)
        results.append(
            TTLResult(
                request_id=req.id,
                url=req.url,
                ttl_seconds=ttl,
                source=source,
            )
        )
    return TTLStats(results=results)
