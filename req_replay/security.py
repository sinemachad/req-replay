"""Security header analysis for captured requests and responses."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from req_replay.models import CapturedRequest, CapturedResponse

SECURITY_HEADERS = {
    "strict-transport-security": "HSTS not set",
    "x-content-type-options": "X-Content-Type-Options not set",
    "x-frame-options": "X-Frame-Options not set",
    "content-security-policy": "Content-Security-Policy not set",
    "referrer-policy": "Referrer-Policy not set",
    "permissions-policy": "Permissions-Policy not set",
}


@dataclass
class SecurityWarning:
    code: str
    message: str
    header: str

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "header": self.header}


@dataclass
class SecurityResult:
    warnings: List[SecurityWarning] = field(default_factory=list)

    def passed(self) -> bool:
        return len(self.warnings) == 0

    def summary(self) -> str:
        if self.passed():
            return "OK – no security header issues"
        lines = [f"  [{w.code}] {w.message}" for w in self.warnings]
        return "Security issues found:\n" + "\n".join(lines)

    def display(self) -> str:
        return self.summary()


def _norm(headers: dict, key: str) -> Optional[str]:
    for k, v in headers.items():
        if k.lower() == key.lower():
            return v
    return None


def analyze_security(
    response: CapturedResponse,
    request: Optional[CapturedRequest] = None,
) -> SecurityResult:
    """Check response headers for missing security headers."""
    warnings: List[SecurityWarning] = []
    headers = response.headers or {}

    for idx, (header, message) in enumerate(SECURITY_HEADERS.items(), start=1):
        if _norm(headers, header) is None:
            code = f"SEC{idx:03d}"
            warnings.append(SecurityWarning(code=code, message=message, header=header))

    # Warn if response is over HTTP and HSTS is present (misconfiguration)
    if request is not None:
        url = request.url or ""
        if url.startswith("http://"):
            hsts = _norm(headers, "strict-transport-security")
            if hsts is not None:
                warnings.append(
                    SecurityWarning(
                        code="SEC007",
                        message="HSTS header sent over plain HTTP",
                        header="strict-transport-security",
                    )
                )

    return SecurityResult(warnings=warnings)
