"""Response caching analysis — detect cache-related headers and summarise caching behaviour."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from req_replay.models import CapturedRequest, CapturedResponse


_CACHE_HEADERS = {
    "cache-control",
    "etag",
    "last-modified",
    "expires",
    "pragma",
    "vary",
    "age",
}


@dataclass
class CacheInfo:
    cache_control: Optional[str] = None
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    expires: Optional[str] = None
    pragma: Optional[str] = None
    vary: Optional[str] = None
    age: Optional[int] = None
    is_cacheable: bool = False
    directives: List[str] = field(default_factory=list)

    def display(self) -> str:
        lines = ["Cache Analysis:"]
        lines.append(f"  Cacheable     : {self.is_cacheable}")
        if self.cache_control:
            lines.append(f"  Cache-Control : {self.cache_control}")
        if self.directives:
            lines.append(f"  Directives    : {', '.join(self.directives)}")
        if self.etag:
            lines.append(f"  ETag          : {self.etag}")
        if self.last_modified:
            lines.append(f"  Last-Modified : {self.last_modified}")
        if self.expires:
            lines.append(f"  Expires       : {self.expires}")
        if self.age is not None:
            lines.append(f"  Age           : {self.age}s")
        if self.vary:
            lines.append(f"  Vary          : {self.vary}")
        return "\n".join(lines)


def _norm(headers: dict) -> dict:
    return {k.lower(): v for k, v in headers.items()}


def _parse_directives(cc: Optional[str]) -> List[str]:
    if not cc:
        return []
    return [d.strip().lower() for d in cc.split(",") if d.strip()]


def analyze_cache(response: CapturedResponse) -> CacheInfo:
    h = _norm(response.headers)
    cc = h.get("cache-control")
    directives = _parse_directives(cc)
    no_store = "no-store" in directives
    private = "private" in directives
    has_expiry = "max-age" in " ".join(directives) or "expires" in h
    is_cacheable = bool(cc) and not no_store and not private and has_expiry
    age_raw = h.get("age")
    age = int(age_raw) if age_raw and age_raw.isdigit() else None
    return CacheInfo(
        cache_control=cc,
        etag=h.get("etag"),
        last_modified=h.get("last-modified"),
        expires=h.get("expires"),
        pragma=h.get("pragma"),
        vary=h.get("vary"),
        age=age,
        is_cacheable=is_cacheable,
        directives=directives,
    )


def summarize_cache(
    pairs: List[Tuple[CapturedRequest, CapturedResponse]],
) -> dict:
    total = len(pairs)
    cacheable = sum(1 for _, r in pairs if analyze_cache(r).is_cacheable)
    return {
        "total": total,
        "cacheable": cacheable,
        "uncacheable": total - cacheable,
        "cacheable_pct": round(cacheable / total * 100, 1) if total else 0.0,
    }
