"""Request timing breakdown analysis."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from req_replay.models import CapturedRequest


@dataclass
class TimingBreakdown:
    request_id: str
    dns_ms: Optional[float]
    connect_ms: Optional[float]
    tls_ms: Optional[float]
    send_ms: Optional[float]
    wait_ms: Optional[float]
    receive_ms: Optional[float]
    total_ms: Optional[float]

    def display(self) -> str:
        lines = [f"Timing breakdown for {self.request_id}:"]
        fields = [
            ("DNS", self.dns_ms),
            ("Connect", self.connect_ms),
            ("TLS", self.tls_ms),
            ("Send", self.send_ms),
            ("Wait", self.wait_ms),
            ("Receive", self.receive_ms),
            ("Total", self.total_ms),
        ]
        for label, val in fields:
            if val is not None:
                lines.append(f"  {label:<10} {val:.2f} ms")
            else:
                lines.append(f"  {label:<10} n/a")
        return "\n".join(lines)


def analyze_timing(request: CapturedRequest) -> TimingBreakdown:
    """Extract timing metadata from a captured request's metadata dict."""
    meta = request.metadata or {}
    timing = meta.get("timing", {})

    def _get(key: str) -> Optional[float]:
        val = timing.get(key)
        return float(val) if val is not None else None

    return TimingBreakdown(
        request_id=request.id,
        dns_ms=_get("dns_ms"),
        connect_ms=_get("connect_ms"),
        tls_ms=_get("tls_ms"),
        send_ms=_get("send_ms"),
        wait_ms=_get("wait_ms"),
        receive_ms=_get("receive_ms"),
        total_ms=_get("total_ms"),
    )


def summarize_timings(requests: List[CapturedRequest]) -> List[TimingBreakdown]:
    """Return timing breakdowns for all requests that have timing metadata."""
    results = []
    for req in requests:
        meta = req.metadata or {}
        if "timing" in meta:
            results.append(analyze_timing(req))
    return results
