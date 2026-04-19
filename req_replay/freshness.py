"""Analyse HTTP response freshness based on cache-control and age headers."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from req_replay.models import CapturedResponse


@dataclass
class FreshnessResult:
    response_id: str
    max_age: Optional[int]  # seconds from Cache-Control: max-age
    age: Optional[int]      # seconds from Age header
    ttl: Optional[int]      # max_age - age, None if unknown
    stale: bool
    warnings: list[str] = field(default_factory=list)

    def display(self) -> str:
        lines = [f"Response : {self.response_id}"]
        lines.append(f"Max-Age  : {self.max_age if self.max_age is not None else 'n/a'}")
        lines.append(f"Age      : {self.age if self.age is not None else 'n/a'}")
        lines.append(f"TTL      : {self.ttl if self.ttl is not None else 'n/a'}")
        lines.append(f"Stale    : {'yes' if self.stale else 'no'}")
        for w in self.warnings:
            lines.append(f"  ! {w}")
        return "\n".join(lines)


def _header(resp: CapturedResponse, name: str) -> Optional[str]:
    for k, v in resp.headers.items():
        if k.lower() == name.lower():
            return v
    return None


def _parse_max_age(cc: str) -> Optional[int]:
    for part in cc.split(","):
        part = part.strip()
        if part.lower().startswith("max-age="):
            try:
                return int(part.split("=", 1)[1])
            except ValueError:
                return None
    return None


def analyze_freshness(response_id: str, resp: CapturedResponse) -> FreshnessResult:
    warnings: list[str] = []
    cc = _header(resp, "cache-control") or ""
    age_raw = _header(resp, "age")

    max_age: Optional[int] = _parse_max_age(cc) if cc else None
    age: Optional[int] = None
    if age_raw is not None:
        try:
            age = int(age_raw)
        except ValueError:
            warnings.append("Age header is not a valid integer")

    ttl: Optional[int] = None
    stale = False

    if max_age is not None and age is not None:
        ttl = max_age - age
        stale = ttl <= 0
    elif max_age is None and cc:
        if "no-store" in cc.lower() or "no-cache" in cc.lower():
            stale = True

    if max_age is None and not cc:
        warnings.append("No Cache-Control header; freshness cannot be determined")

    return FreshnessResult(
        response_id=response_id,
        max_age=max_age,
        age=age,
        ttl=ttl,
        stale=stale,
        warnings=warnings,
    )
