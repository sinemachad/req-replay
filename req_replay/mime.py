"""MIME type analysis for captured requests and responses."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple
from collections import Counter

from req_replay.models import CapturedRequest, CapturedResponse


@dataclass
class MimeStats:
    request_types: Counter = field(default_factory=Counter)
    response_types: Counter = field(default_factory=Counter)
    total_requests: int = 0
    total_responses: int = 0

    def top_request_types(self, n: int = 5) -> List[Tuple[str, int]]:
        return self.request_types.most_common(n)

    def top_response_types(self, n: int = 5) -> List[Tuple[str, int]]:
        return self.response_types.most_common(n)

    def display(self) -> str:
        lines = ["MIME Type Analysis"]
        lines.append(f"  Requests : {self.total_requests}")
        for mime, count in self.top_request_types():
            lines.append(f"    {mime}: {count}")
        lines.append(f"  Responses: {self.total_responses}")
        for mime, count in self.top_response_types():
            lines.append(f"    {mime}: {count}")
        return "\n".join(lines)


def _extract_mime(headers: dict, key: str = "content-type") -> str:
    for k, v in headers.items():
        if k.lower() == key:
            return v.split(";")[0].strip().lower()
    return "unknown"


def analyze_mime(
    pairs: List[Tuple[CapturedRequest, CapturedResponse]],
) -> MimeStats:
    stats = MimeStats()
    for req, resp in pairs:
        req_mime = _extract_mime(req.headers)
        resp_mime = _extract_mime(resp.headers)
        if req.body:
            stats.request_types[req_mime] += 1
            stats.total_requests += 1
        if resp.body:
            stats.response_types[resp_mime] += 1
            stats.total_responses += 1
    return stats
