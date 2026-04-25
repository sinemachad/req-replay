"""Analyse and enforce header key casing conventions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from req_replay.models import CapturedRequest


@dataclass
class CasingWarning:
    code: str
    header: str
    expected: str
    actual: str

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "header": self.header,
            "expected": self.expected,
            "actual": self.actual,
        }


@dataclass
class CasingResult:
    request_id: str
    warnings: List[CasingWarning] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.warnings) == 0

    def summary(self) -> str:
        if self.passed:
            return f"{self.request_id}: OK"
        codes = ", ".join(w.code for w in self.warnings)
        return f"{self.request_id}: FAIL [{codes}]"


def _to_title_case(key: str) -> str:
    """Convert a header key to HTTP/1.1 Title-Case."""
    return "-".join(part.capitalize() for part in key.split("-"))


def analyze_casing(
    request: CapturedRequest,
    convention: str = "title",
) -> CasingResult:
    """Check header key casing against *convention*.

    Supported conventions:
      - ``"title"``  – Title-Case  (e.g. ``Content-Type``)
      - ``"lower"``  – all-lowercase (e.g. ``content-type``)
    """
    warnings: List[CasingWarning] = []
    headers: Dict[str, str] = request.headers or {}

    for key in headers:
        if convention == "lower":
            expected = key.lower()
        else:
            expected = _to_title_case(key)

        if key != expected:
            warnings.append(
                CasingWarning(
                    code="HC001",
                    header=key,
                    expected=expected,
                    actual=key,
                )
            )

    return CasingResult(request_id=request.id, warnings=warnings)
