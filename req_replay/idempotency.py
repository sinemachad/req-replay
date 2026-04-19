"""Idempotency analysis: detect non-idempotent request patterns."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
from req_replay.models import CapturedRequest

NON_IDEMPOTENT_METHODS = {"POST"}
IDEMPOTENT_METHODS = {"GET", "HEAD", "PUT", "DELETE", "OPTIONS", "TRACE"}


@dataclass
class IdempotencyWarning:
    code: str
    method: str
    url: str
    message: str

    def to_dict(self) -> dict:
        return {"code": self.code, "method": self.method, "url": self.url, "message": self.message}


@dataclass
class IdempotencyResult:
    warnings: List[IdempotencyWarning] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.warnings) == 0

    @property
    def summary(self) -> str:
        if self.passed:
            return "OK — no idempotency issues detected"
        return f"{len(self.warnings)} idempotency warning(s) found"

    def display(self) -> str:
        lines = [self.summary]
        for w in self.warnings:
            lines.append(f"  [{w.code}] {w.method} {w.url} — {w.message}")
        return "\n".join(lines)


def analyze_idempotency(requests: List[CapturedRequest]) -> IdempotencyResult:
    """Analyse a list of requests for idempotency concerns."""
    warnings: List[IdempotencyWarning] = []
    seen: Dict[str, int] = {}

    for req in requests:
        method = req.method.upper()
        key = f"{method}:{req.url}"

        if method in NON_IDEMPOTENT_METHODS:
            count = seen.get(key, 0) + 1
            seen[key] = count
            if count > 1:
                warnings.append(IdempotencyWarning(
                    code="I001",
                    method=method,
                    url=req.url,
                    message=f"Repeated {method} to same URL ({count}x) — may cause duplicate side-effects",
                ))

        if method in NON_IDEMPOTENT_METHODS and not req.body:
            warnings.append(IdempotencyWarning(
                code="I002",
                method=method,
                url=req.url,
                message=f"{method} request has no body — likely unintentional",
            ))

    return IdempotencyResult(warnings=warnings)
