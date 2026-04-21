"""Header whitelist enforcement — warn when requests contain headers not in an allowed set."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from req_replay.models import CapturedRequest

_DEFAULT_ALLOWED: frozenset[str] = frozenset({
    "accept",
    "accept-encoding",
    "accept-language",
    "authorization",
    "cache-control",
    "content-length",
    "content-type",
    "host",
    "user-agent",
    "x-request-id",
    "x-correlation-id",
})


@dataclass
class WhitelistWarning:
    code: str
    header: str
    message: str

    def to_dict(self) -> dict:
        return {"code": self.code, "header": self.header, "message": self.message}


@dataclass
class WhitelistResult:
    request_id: str
    warnings: list[WhitelistWarning] = field(default_factory=list)

    def passed(self) -> bool:
        return len(self.warnings) == 0

    def summary(self) -> str:
        if self.passed():
            return f"{self.request_id}: OK — all headers are whitelisted"
        codes = ", ".join(w.code for w in self.warnings)
        return f"{self.request_id}: FAIL [{codes}]"

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "passed": self.passed(),
            "warnings": [w.to_dict() for w in self.warnings],
        }


def check_whitelist(
    request: CapturedRequest,
    allowed: Iterable[str] | None = None,
) -> WhitelistResult:
    """Return a WhitelistResult for *request* given the *allowed* header set."""
    allowed_set: frozenset[str] = (
        frozenset(h.lower() for h in allowed) if allowed is not None else _DEFAULT_ALLOWED
    )
    warnings: list[WhitelistWarning] = []
    for key in (request.headers or {}):
        if key.lower() not in allowed_set:
            warnings.append(
                WhitelistWarning(
                    code="HW001",
                    header=key,
                    message=f"Header '{key}' is not in the allowed whitelist",
                )
            )
    return WhitelistResult(request_id=request.id, warnings=warnings)


def scan_whitelist(
    requests: list[CapturedRequest],
    allowed: Iterable[str] | None = None,
) -> list[WhitelistResult]:
    """Run whitelist check across multiple requests."""
    return [check_whitelist(r, allowed) for r in requests]
