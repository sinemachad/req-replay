"""Detect anomalous requests based on simple statistical thresholds."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from statistics import mean, stdev

from req_replay.models import CapturedRequest


@dataclass
class AnomalyWarning:
    request_id: str
    field: str
    message: str

    def to_dict(self) -> dict:
        return {"request_id": self.request_id, "field": self.field, "message": self.message}


@dataclass
class AnomalyResult:
    warnings: List[AnomalyWarning] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.warnings) == 0

    def summary(self) -> str:
        if self.passed:
            return "No anomalies detected."
        lines = [f"  [{w.field}] {w.message}" for w in self.warnings]
        return "Anomalies detected:\n" + "\n".join(lines)


def _body_len(req: CapturedRequest) -> int:
    return len(req.body.encode() if isinstance(req.body, str) else (req.body or b""))


def analyze_anomalies(
    requests: List[CapturedRequest],
    z_threshold: float = 2.5,
) -> AnomalyResult:
    """Flag requests whose body size or header count deviate significantly from the mean."""
    if len(requests) < 3:
        return AnomalyResult()

    sizes = [_body_len(r) for r in requests]
    header_counts = [len(r.headers) for r in requests]

    warnings: List[AnomalyWarning] = []

    for metric_name, values in (("body_size", sizes), ("header_count", header_counts)):
        mu = mean(values)
        sd = stdev(values)
        if sd == 0:
            continue
        for req, val in zip(requests, values):
            z = abs(val - mu) / sd
            if z > z_threshold:
                warnings.append(
                    AnomalyWarning(
                        request_id=req.id,
                        field=metric_name,
                        message=(
                            f"{metric_name}={val} deviates {z:.2f} standard deviations "
                            f"from mean {mu:.1f} (threshold {z_threshold})"
                        ),
                    )
                )

    return AnomalyResult(warnings=warnings)
