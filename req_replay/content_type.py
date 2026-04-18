"""Analyse Content-Type distribution across captured requests/responses."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Tuple

from req_replay.models import CapturedRequest, CapturedResponse


@dataclass
class ContentTypeStats:
    request_types: Counter = field(default_factory=Counter)
    response_types: Counter = field(default_factory=Counter)

    @property
    def total_requests(self) -> int:
        return sum(self.request_types.values())

    @property
    def total_responses(self) -> int:
        return sum(self.response_types.values())

    def top_request_types(self, n: int = 5) -> List[Tuple[str, int]]:
        return self.request_types.most_common(n)

    def top_response_types(self, n: int = 5) -> List[Tuple[str, int]]:
        return self.response_types.most_common(n)

    def display(self) -> str:
        lines = ["Content-Type Analysis", "=" * 40]
        lines.append("Request Content-Types:")
        for ct, count in self.top_request_types():
            lines.append(f"  {ct}: {count}")
        if not self.request_types:
            lines.append("  (none)")
        lines.append("Response Content-Types:")
        for ct, count in self.top_response_types():
            lines.append(f"  {ct}: {count}")
        if not self.response_types:
            lines.append("  (none)")
        return "\n".join(lines)


def _extract_content_type(headers: dict) -> str:
    for key, value in headers.items():
        if key.lower() == "content-type":
            return value.split(";")[0].strip().lower()
    return "(none)"


def analyze_content_types(
    pairs: List[Tuple[CapturedRequest, CapturedResponse]],
) -> ContentTypeStats:
    stats = ContentTypeStats()
    for req, resp in pairs:
        stats.request_types[_extract_content_type(req.headers)] += 1
        stats.response_types[_extract_content_type(resp.headers)] += 1
    return stats
