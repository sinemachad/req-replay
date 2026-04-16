"""Lint captured requests for common issues and best practices."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from req_replay.models import CapturedRequest


@dataclass
class LintWarning:
    code: str
    message: str
    severity: str = "warning"  # "warning" | "error"

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "severity": self.severity}


@dataclass
class LintResult:
    request_id: str
    warnings: List[LintWarning] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(w.severity == "error" for w in self.warnings)

    @property
    def summary(self) -> str:
        if not self.warnings:
            return f"{self.request_id}: OK"
        lines = [f"{self.request_id}: {len(self.warnings)} issue(s)"]
        for w in self.warnings:
            lines.append(f"  [{w.severity.upper()}] {w.code}: {w.message}")
        return "\n".join(lines)


def lint_request(req: CapturedRequest) -> LintResult:
    """Run all lint checks against a captured request and return a LintResult."""
    warnings: List[LintWarning] = []

    # L001 – missing Content-Type on POST/PUT/PATCH
    method = req.method.upper()
    headers_lower = {k.lower(): v for k, v in req.headers.items()}
    if method in ("POST", "PUT", "PATCH") and "content-type" not in headers_lower:
        warnings.append(
            LintWarning(
                code="L001",
                message=f"{method} request is missing a Content-Type header.",
                severity="warning",
            )
        )

    # L002 – Authorization header contains a bare token (no scheme)
    auth = headers_lower.get("authorization", "")
    if auth and " " not in auth.strip():
        warnings.append(
            LintWarning(
                code="L002",
                message="Authorization header value has no scheme (e.g. 'Bearer <token>').",
                severity="warning",
            )
        )

    # L003 – URL contains credentials
    if "@" in req.url.split("?")[0]:
        warnings.append(
            LintWarning(
                code="L003",
                message="URL appears to contain embedded credentials.",
                severity="error",
            )
        )

    # L004 – plain HTTP (not HTTPS)
    if req.url.startswith("http://"):
        warnings.append(
            LintWarning(
                code="L004",
                message="Request uses plain HTTP instead of HTTPS.",
                severity="warning",
            )
        )

    # L005 – no tags set
    if not req.tags:
        warnings.append(
            LintWarning(
                code="L005",
                message="Request has no tags; consider tagging for easier filtering.",
                severity="warning",
            )
        )

    return LintResult(request_id=req.id, warnings=warnings)
