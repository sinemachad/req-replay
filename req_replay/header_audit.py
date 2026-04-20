"""Header audit: detect common header hygiene issues across captured requests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from req_replay.models import CapturedRequest

_SENSITIVE_HEADERS = {"authorization", "x-api-key", "x-auth-token", "cookie", "set-cookie"}
_RECOMMENDED_HEADERS = {"content-type", "accept", "user-agent"}


@dataclass
class HeaderAuditWarning:
    code: str
    header: Optional[str]
    message: str

    def to_dict(self) -> dict:
        return {"code": self.code, "header": self.header, "message": self.message}


@dataclass
class HeaderAuditResult:
    request_id: str
    warnings: List[HeaderAuditWarning] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.warnings) == 0

    @property
    def summary(self) -> str:
        if self.passed:
            return f"{self.request_id}: OK"
        codes = ", ".join(w.code for w in self.warnings)
        return f"{self.request_id}: {len(self.warnings)} warning(s) [{codes}]"


def audit_headers(request: CapturedRequest) -> HeaderAuditResult:
    """Audit a single request for header hygiene issues."""
    warnings: List[HeaderAuditWarning] = []
    lower_keys = {k.lower(): v for k, v in (request.headers or {}).items()}

    # HA001: sensitive header present in plaintext store
    for sensitive in _SENSITIVE_HEADERS:
        if sensitive in lower_keys:
            warnings.append(HeaderAuditWarning(
                code="HA001",
                header=sensitive,
                message=f"Sensitive header '{sensitive}' is present; consider redacting before storage.",
            ))

    # HA002: missing recommended headers
    for recommended in _RECOMMENDED_HEADERS:
        if recommended not in lower_keys:
            warnings.append(HeaderAuditWarning(
                code="HA002",
                header=recommended,
                message=f"Recommended header '{recommended}' is absent.",
            ))

    # HA003: empty header value
    for key, value in (request.headers or {}).items():
        if value == "" or value is None:
            warnings.append(HeaderAuditWarning(
                code="HA003",
                header=key.lower(),
                message=f"Header '{key}' has an empty value.",
            ))

    return HeaderAuditResult(request_id=request.id, warnings=warnings)


def audit_all(requests: List[CapturedRequest]) -> List[HeaderAuditResult]:
    """Audit a list of requests, returning one result per request."""
    return [audit_headers(r) for r in requests]
