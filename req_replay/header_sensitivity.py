"""Detect potentially sensitive headers in captured requests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

# Headers that commonly carry sensitive values
_SENSITIVE_PATTERNS: List[str] = [
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
    "x-secret",
    "x-access-token",
    "x-csrf-token",
    "api-key",
    "secret",
    "token",
    "password",
    "passwd",
]


@dataclass
class SensitivityWarning:
    code: str
    header: str
    message: str

    def to_dict(self) -> dict:
        return {"code": self.code, "header": self.header, "message": self.message}


@dataclass
class SensitivityResult:
    request_id: str
    warnings: List[SensitivityWarning] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.warnings) == 0

    def summary(self) -> str:
        if self.passed:
            return f"{self.request_id}: OK – no sensitive headers detected"
        codes = ", ".join(w.code for w in self.warnings)
        return f"{self.request_id}: WARN – sensitive headers detected ({codes})"

    def display(self) -> str:
        lines = [self.summary()]
        for w in self.warnings:
            lines.append(f"  [{w.code}] {w.header}: {w.message}")
        return "\n".join(lines)


def analyze_sensitivity(
    request_id: str,
    headers: Dict[str, str],
    extra_patterns: List[str] | None = None,
) -> SensitivityResult:
    """Check *headers* for sensitive keys and return a SensitivityResult."""
    patterns = _SENSITIVE_PATTERNS + [p.lower() for p in (extra_patterns or [])]
    warnings: List[SensitivityWarning] = []

    for key in headers:
        normalised = key.lower()
        if any(pat in normalised for pat in patterns):
            warnings.append(
                SensitivityWarning(
                    code="HS001",
                    header=key,
                    message=f"Header '{key}' may carry sensitive data and should be redacted before storage.",
                )
            )

    return SensitivityResult(request_id=request_id, warnings=warnings)
