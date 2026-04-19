"""Detect duplicate or conflicting headers in captured requests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from req_replay.models import CapturedRequest


@dataclass
class DuplicateHeaderWarning:
    code: str
    header: str
    message: str

    def to_dict(self) -> dict:
        return {"code": self.code, "header": self.header, "message": self.message}


@dataclass
class DuplicateHeaderResult:
    request_id: str
    warnings: List[DuplicateHeaderWarning] = field(default_factory=list)

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
            lines.append(f"  [{w.code}] {w.header}: {w.message}")
        return "\n".join(lines)


def analyze_duplicate_headers(request: CapturedRequest) -> DuplicateHeaderResult:
    """Detect duplicate or conflicting header keys (case-insensitive)."""
    warnings: List[DuplicateHeaderWarning] = []
    seen: Dict[str, List[str]] = {}

    for key, value in request.headers.items():
        norm = key.lower()
        seen.setdefault(norm, []).append(value)

    for norm_key, values in seen.items():
        if len(values) > 1:
            warnings.append(
                DuplicateHeaderWarning(
                    code="DH001",
                    header=norm_key,
                    message=f"Header '{norm_key}' appears {len(values)} times with values: {values}",
                )
            )

    # Check for conflicting content-type vs accept
    ct = seen.get("content-type", [])
    if len(ct) == 1 and "accept" in seen:
        accept_vals = seen["accept"]
        ct_base = ct[0].split(";")[0].strip()
        if ct_base and all(ct_base not in a for a in accept_vals) and "*/*" not in " ".join(accept_vals):
            warnings.append(
                DuplicateHeaderWarning(
                    code="DH002",
                    header="content-type / accept",
                    message=f"Content-Type '{ct_base}' not represented in Accept header(s): {accept_vals}",
                )
            )

    return DuplicateHeaderResult(request_id=request.id, warnings=warnings)


def scan_duplicate_headers(requests: List[CapturedRequest]) -> List[DuplicateHeaderResult]:
    return [analyze_duplicate_headers(r) for r in requests]
