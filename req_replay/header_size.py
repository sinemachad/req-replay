"""Analyse the total byte size of headers across captured requests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from req_replay.models import CapturedRequest


@dataclass
class HeaderSizeStats:
    total_requests: int = 0
    min_bytes: Optional[int] = None
    max_bytes: Optional[int] = None
    mean_bytes: float = 0.0
    over_threshold: int = 0
    by_request: Dict[str, int] = field(default_factory=dict)

    def display(self) -> str:  # pragma: no cover
        lines = [
            f"Requests analysed : {self.total_requests}",
            f"Min header size   : {self.min_bytes} bytes",
            f"Max header size   : {self.max_bytes} bytes",
            f"Mean header size  : {self.mean_bytes:.1f} bytes",
            f"Over threshold    : {self.over_threshold}",
        ]
        return "\n".join(lines)


def _header_bytes(request: CapturedRequest) -> int:
    """Return the total byte length of all header keys and values."""
    total = 0
    for k, v in (request.headers or {}).items():
        total += len(k.encode("utf-8")) + len(v.encode("utf-8"))
    return total


def analyze_header_sizes(
    requests: List[CapturedRequest],
    threshold: int = 8192,
) -> HeaderSizeStats:
    """Compute header size statistics for a list of requests."""
    if not requests:
        return HeaderSizeStats()

    sizes: List[int] = []
    by_request: Dict[str, int] = {}

    for req in requests:
        size = _header_bytes(req)
        sizes.append(size)
        by_request[req.id] = size

    over = sum(1 for s in sizes if s > threshold)

    return HeaderSizeStats(
        total_requests=len(sizes),
        min_bytes=min(sizes),
        max_bytes=max(sizes),
        mean_bytes=sum(sizes) / len(sizes),
        over_threshold=over,
        by_request=by_request,
    )
