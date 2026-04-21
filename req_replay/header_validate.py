"""Validate request headers against common rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from req_replay.models import CapturedRequest

_VALID_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE"}

_CONTENT_TYPE_METHODS = {"POST", "PUT", "PATCH"}


@dataclass
class HeaderValidationWarning:
    code: str
    message: str
    header: Optional[str] = None

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "header": self.header}


@dataclass
class HeaderValidationResult:
    request_id: str
    warnings: List[HeaderValidationWarning] = field(default_factory=list)

    def passed(self) -> bool:
        return len(self.warnings) == 0

    def summary(self) -> str:
        if self.passed():
            return f"{self.request_id}: OK"
        codes = ", ".join(w.code for w in self.warnings)
        return f"{self.request_id}: {len(self.warnings)} warning(s) [{codes}]"

    def display(self) -> str:
        lines = [self.summary()]
        for w in self.warnings:
            hdr = f" (header: {w.header})" if w.header else ""
            lines.append(f"  [{w.code}] {w.message}{hdr}")
        return "\n".join(lines)


def validate_request_headers(request: CapturedRequest) -> HeaderValidationResult:
    """Run header validation checks and return a result with any warnings."""
    warnings: List[HeaderValidationWarning] = []
    headers_lower = {k.lower(): v for k, v in (request.headers or {}).items()}

    # HV001: Content-Type required for body-bearing methods
    if request.method.upper() in _CONTENT_TYPE_METHODS and request.body:
        if "content-type" not in headers_lower:
            warnings.append(HeaderValidationWarning(
                code="HV001",
                message="Content-Type header is required when a body is present",
                header="content-type",
            ))

    # HV002: Content-Length should not be set manually (may conflict with transport)
    if "content-length" in headers_lower:
        warnings.append(HeaderValidationWarning(
            code="HV002",
            message="Content-Length should not be set manually; let the transport layer handle it",
            header="content-length",
        ))

    # HV003: Host header must be present
    if "host" not in headers_lower:
        warnings.append(HeaderValidationWarning(
            code="HV003",
            message="Host header is missing",
            header="host",
        ))

    # HV004: Authorization header value should not be empty
    if "authorization" in headers_lower and not headers_lower["authorization"].strip():
        warnings.append(HeaderValidationWarning(
            code="HV004",
            message="Authorization header is present but empty",
            header="authorization",
        ))

    return HeaderValidationResult(request_id=request.id, warnings=warnings)
