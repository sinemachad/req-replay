"""Summarize a collection of captured requests/responses into stats."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional

from req_replay.models import CapturedRequest, CapturedResponse


@dataclass
class RequestSummary:
    total: int = 0
    by_method: dict = field(default_factory=dict)
    by_status: dict = field(default_factory=dict)
    by_host: dict = field(default_factory=dict)
    avg_response_size_bytes: float = 0.0
    error_rate: float = 0.0  # fraction of 5xx responses

    def display(self) -> str:
        lines = [
            f"Total requests : {self.total}",
            f"By method      : {dict(sorted(self.by_method.items()))}",
            f"By status      : {dict(sorted(self.by_status.items()))}",
            f"By host        : {dict(sorted(self.by_host.items()))}",
            f"Avg body size  : {self.avg_response_size_bytes:.1f} bytes",
            f"Error rate     : {self.error_rate * 100:.1f}%",
        ]
        return "\n".join(lines)


def summarize(
    pairs: List[tuple[CapturedRequest, Optional[CapturedResponse]]],
) -> RequestSummary:
    """Compute summary statistics from a list of (request, response) pairs.

    *response* may be ``None`` if only requests are available.
    """
    if not pairs:
        return RequestSummary()

    method_counter: Counter = Counter()
    status_counter: Counter = Counter()
    host_counter: Counter = Counter()
    total_bytes = 0
    error_count = 0
    response_count = 0

    for req, resp in pairs:
        method_counter[req.method.upper()] += 1

        from urllib.parse import urlparse
        host = urlparse(req.url).netloc or req.url
        host_counter[host] += 1

        if resp is not None:
            response_count += 1
            status_counter[resp.status_code] += 1
            if resp.body:
                total_bytes += len(resp.body.encode("utf-8", errors="replace"))
            if resp.status_code >= 500:
                error_count += 1

    avg_size = total_bytes / response_count if response_count else 0.0
    error_rate = error_count / response_count if response_count else 0.0

    return RequestSummary(
        total=len(pairs),
        by_method=dict(method_counter),
        by_status=dict(status_counter),
        by_host=dict(host_counter),
        avg_response_size_bytes=avg_size,
        error_rate=error_rate,
    )
