"""Boundary analysis: detect requests that cross environment boundaries (e.g. HTTP→HTTPS, internal→external)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Sequence, Tuple
from urllib.parse import urlparse

from req_replay.models import CapturedRequest


@dataclass
class BoundaryWarning:
    request_id: str
    url: str
    code: str
    message: str

    def to_dict(self) -> dict:
        return {"request_id": self.request_id, "url": self.url, "code": self.code, "message": self.message}


@dataclass
class BoundaryResult:
    warnings: List[BoundaryWarning] = field(default_factory=list)

    def passed(self) -> bool:
        return len(self.warnings) == 0

    def summary(self) -> str:
        if self.passed():
            return "OK – no boundary issues detected"
        return f"{len(self.warnings)} boundary warning(s) found"

    def display(self) -> str:
        lines = [self.summary()]
        for w in self.warnings:
            lines.append(f"  [{w.code}] {w.url} – {w.message}")
        return "\n".join(lines)


def _is_internal(host: str) -> bool:
    internal_suffixes = (".local", ".internal", ".corp", ".lan")
    internal_prefixes = ("10.", "192.168.", "172.")
    return any(host.endswith(s) for s in internal_suffixes) or any(host.startswith(p) for p in internal_prefixes)


def analyze_boundaries(requests: Sequence[CapturedRequest]) -> BoundaryResult:
    warnings: List[BoundaryWarning] = []
    for req in requests:
        parsed = urlparse(req.url)
        scheme = (parsed.scheme or "").lower()
        host = (parsed.hostname or "").lower()

        if scheme == "http":
            warnings.append(BoundaryWarning(
                request_id=req.id,
                url=req.url,
                code="B001",
                message="Request uses plain HTTP instead of HTTPS",
            ))

        if not _is_internal(host) and host:
            method = (req.method or "").upper()
            if method in {"POST", "PUT", "PATCH", "DELETE"}:
                warnings.append(BoundaryWarning(
                    request_id=req.id,
                    url=req.url,
                    code="B002",
                    message=f"Mutating {method} request sent to external host '{host}'",
                ))

    return BoundaryResult(warnings=warnings)
