"""Request quota tracking — flag when a request ID exceeds a call budget."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from req_replay.models import CapturedRequest


@dataclass
class QuotaWarning:
    code: str
    message: str

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message}


@dataclass
class QuotaResult:
    request_id: str
    call_count: int
    limit: int
    warnings: List[QuotaWarning] = field(default_factory=list)

    def passed(self) -> bool:
        return len(self.warnings) == 0

    def summary(self) -> str:
        if self.passed():
            return f"{self.request_id}: {self.call_count}/{self.limit} calls — OK"
        return f"{self.request_id}: {self.call_count}/{self.limit} calls — {len(self.warnings)} warning(s)"


def analyze_quota(
    requests: List[CapturedRequest],
    limit: int = 100,
) -> List[QuotaResult]:
    """Count replays per request_id and warn when the limit is reached or exceeded."""
    counts: Dict[str, int] = {}
    for req in requests:
        counts[req.id] = counts.get(req.id, 0) + 1

    results: List[QuotaResult] = []
    for req_id, count in counts.items():
        warnings: List[QuotaWarning] = []
        if count >= limit:
            warnings.append(
                QuotaWarning(
                    code="Q001",
                    message=(
                        f"Request '{req_id}' has been replayed {count} time(s), "
                        f"meeting or exceeding the limit of {limit}."
                    ),
                )
            )
        results.append(QuotaResult(request_id=req_id, call_count=count, limit=limit, warnings=warnings))
    return results
