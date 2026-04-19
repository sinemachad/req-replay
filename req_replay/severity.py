"""Severity classification for captured requests based on response status."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple
from req_replay.models import CapturedRequest, CapturedResponse


LEVEL_OK = "ok"
LEVEL_WARNING = "warning"
LEVEL_ERROR = "error"
LEVEL_CRITICAL = "critical"


@dataclass
class SeverityResult:
    request_id: str
    status_code: int
    level: str
    reason: str

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "status_code": self.status_code,
            "level": self.level,
            "reason": self.reason,
        }

    def display(self) -> str:
        return f"[{self.level.upper()}] {self.request_id} — HTTP {self.status_code}: {self.reason}"


def classify(status_code: int) -> Tuple[str, str]:
    """Return (level, reason) for a given HTTP status code."""
    if status_code < 400:
        return LEVEL_OK, "Successful response"
    if status_code == 401:
        return LEVEL_WARNING, "Unauthorized"
    if status_code == 403:
        return LEVEL_WARNING, "Forbidden"
    if status_code == 404:
        return LEVEL_WARNING, "Not Found"
    if 400 <= status_code < 500:
        return LEVEL_ERROR, f"Client error {status_code}"
    if 500 <= status_code < 600:
        return LEVEL_CRITICAL, f"Server error {status_code}"
    return LEVEL_OK, "Unknown"


def analyze_severity(
    pairs: List[Tuple[CapturedRequest, CapturedResponse]],
) -> List[SeverityResult]:
    results = []
    for req, resp in pairs:
        level, reason = classify(resp.status_code)
        results.append(
            SeverityResult(
                request_id=req.id,
                status_code=resp.status_code,
                level=level,
                reason=reason,
            )
        )
    return results


def severity_summary(results: List[SeverityResult]) -> str:
    counts = {LEVEL_OK: 0, LEVEL_WARNING: 0, LEVEL_ERROR: 0, LEVEL_CRITICAL: 0}
    for r in results:
        counts[r.level] = counts.get(r.level, 0) + 1
    total = len(results)
    return (
        f"Total: {total} | OK: {counts[LEVEL_OK]} | "
        f"Warning: {counts[LEVEL_WARNING]} | Error: {counts[LEVEL_ERROR]} | "
        f"Critical: {counts[LEVEL_CRITICAL]}"
    )
