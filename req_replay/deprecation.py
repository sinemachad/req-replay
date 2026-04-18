"""Detect and report deprecated HTTP headers and patterns in captured requests/responses."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from req_replay.models import CapturedRequest, CapturedResponse

# Headers considered deprecated or discouraged
_DEPRECATED_REQUEST_HEADERS = {
    "x-forwarded-host": "Use the Host header directly.",
    "pragma": "Use Cache-Control instead.",
    "expires": "Use Cache-Control max-age instead (in requests).",
}

_DEPRECATED_RESPONSE_HEADERS = {
    "x-xss-protection": "Superseded by Content-Security-Policy.",
    "pragma": "Use Cache-Control instead.",
    "p3p": "P3P is obsolete and ignored by modern browsers.",
    "x-ua-compatible": "IE compatibility mode header; no longer needed.",
    "expires": "Prefer Cache-Control max-age.",
}


@dataclass
class DeprecationWarning_:  # noqa: N801  (avoid shadowing builtin name)
    source: str  # 'request' or 'response'
    header: str
    reason: str

    def to_dict(self) -> dict:
        return {"source": self.source, "header": self.header, "reason": self.reason}


@dataclass
class DeprecationResult:
    warnings: List[DeprecationWarning_] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.warnings) == 0

    def summary(self) -> str:
        if self.passed:
            return "No deprecated headers detected."
        lines = [f"  [{w.source}] {w.header}: {w.reason}" for w in self.warnings]
        return "Deprecated headers found:\n" + "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "warnings": [w.to_dict() for w in self.warnings],
        }


def check_deprecations(
    request: CapturedRequest,
    response: CapturedResponse | None = None,
) -> DeprecationResult:
    """Check request (and optional response) headers for deprecated usage."""
    warnings: List[DeprecationWarning_] = []

    req_headers_lower = {k.lower(): k for k in (request.headers or {})}
    for deprecated, reason in _DEPRECATED_REQUEST_HEADERS.items():
        if deprecated in req_headers_lower:
            warnings.append(DeprecationWarning_(source="request", header=deprecated, reason=reason))

    if response is not None:
        resp_headers_lower = {k.lower(): k for k in (response.headers or {})}
        for deprecated, reason in _DEPRECATED_RESPONSE_HEADERS.items():
            if deprecated in resp_headers_lower:
                warnings.append(DeprecationWarning_(source="response", header=deprecated, reason=reason))

    return DeprecationResult(warnings=warnings)
