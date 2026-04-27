"""Detect headers that appear on a configurable blacklist."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set

from req_replay.models import CapturedRequest

# Default headers that should never be forwarded / stored
_DEFAULT_BLACKLIST: Set[str] = {
    "proxy-authorization",
    "proxy-authenticate",
    "www-authenticate",
    "x-forwarded-for",
    "x-real-ip",
    "x-cluster-client-ip",
}


@dataclass
class BlacklistWarning:
    code: str
    header: str
    message: str

    def to_dict(self) -> dict:
        return {"code": self.code, "header": self.header, "message": self.message}


@dataclass
class BlacklistResult:
    request_id: str
    warnings: List[BlacklistWarning] = field(default_factory=list)

    def passed(self) -> bool:
        return len(self.warnings) == 0

    def summary(self) -> str:
        if self.passed():
            return "OK – no blacklisted headers found"
        codes = ", ".join(w.code for w in self.warnings)
        return f"FAIL – blacklisted headers detected: {codes}"

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "passed": self.passed(),
            "warnings": [w.to_dict() for w in self.warnings],
        }


def check_blacklist(
    request: CapturedRequest,
    blacklist: Set[str] | None = None,
) -> BlacklistResult:
    """Return a BlacklistResult for *request* against *blacklist*."""
    effective = {h.lower() for h in (blacklist if blacklist is not None else _DEFAULT_BLACKLIST)}
    warnings: List[BlacklistWarning] = []
    for key in request.headers:
        if key.lower() in effective:
            warnings.append(
                BlacklistWarning(
                    code="BL001",
                    header=key,
                    message=f"Header '{key}' is on the blacklist and should not be present.",
                )
            )
    return BlacklistResult(request_id=request.id, warnings=warnings)


def scan_blacklist(
    requests: List[CapturedRequest],
    blacklist: Set[str] | None = None,
) -> List[BlacklistResult]:
    """Scan a list of requests and return one result per request."""
    return [check_blacklist(r, blacklist) for r in requests]
