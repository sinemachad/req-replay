"""Detect deprecated or legacy HTTP headers in captured requests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from req_replay.models import CapturedRequest

# Headers considered deprecated or legacy
_DEPRECATED_HEADERS: dict[str, str] = {
    "x-forwarded-host": "Use the Host header instead",
    "x-http-method-override": "Use the correct HTTP method directly",
    "x-wap-profile": "Obsolete WAP header",
    "pragma": "Use Cache-Control instead",
    "expires": "Prefer Cache-Control: max-age",
    "p3p": "P3P is no longer supported by modern browsers",
    "www-authenticate": "Consider modern auth mechanisms",
    "proxy-connection": "Use Connection header instead",
}


@dataclass
class HeaderDeprecationWarning:
    code: str
    header: str
    message: str
    suggestion: str

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "header": self.header,
            "message": self.message,
            "suggestion": self.suggestion,
        }


@dataclass
class HeaderDeprecationResult:
    request_id: Optional[str]
    warnings: List[HeaderDeprecationWarning] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.warnings) == 0

    def summary(self) -> str:
        if self.passed:
            return "OK – no deprecated headers detected"
        codes = ", ".join(w.code for w in self.warnings)
        return f"WARN – deprecated headers found: {codes}"

    def display(self) -> str:
        lines = [self.summary()]
        for w in self.warnings:
            lines.append(f"  [{w.code}] {w.header}: {w.message} — {w.suggestion}")
        return "\n".join(lines)


def check_deprecated_headers(
    request: CapturedRequest,
    extra_deprecated: Optional[dict[str, str]] = None,
) -> HeaderDeprecationResult:
    """Check a single request for deprecated headers."""
    deprecated = dict(_DEPRECATED_HEADERS)
    if extra_deprecated:
        deprecated.update({k.lower(): v for k, v in extra_deprecated.items()})

    warnings: List[HeaderDeprecationWarning] = []
    for raw_key in (request.headers or {}):
        key = raw_key.lower()
        if key in deprecated:
            warnings.append(
                HeaderDeprecationWarning(
                    code="HD001",
                    header=raw_key,
                    message=f"Header '{raw_key}' is deprecated",
                    suggestion=deprecated[key],
                )
            )

    return HeaderDeprecationResult(
        request_id=getattr(request, "id", None),
        warnings=warnings,
    )


def scan_deprecated_headers(
    requests: List[CapturedRequest],
    extra_deprecated: Optional[dict[str, str]] = None,
) -> List[HeaderDeprecationResult]:
    """Scan a list of requests for deprecated headers."""
    return [check_deprecated_headers(r, extra_deprecated) for r in requests]
