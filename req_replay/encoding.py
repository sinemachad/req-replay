"""Analyze content-encoding and transfer-encoding headers in captured requests/responses."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from collections import Counter

from req_replay.models import CapturedRequest, CapturedResponse

COMMON_ENCODINGS = {"gzip", "deflate", "br", "identity", "compress", "chunked"}


@dataclass
class EncodingStats:
    total_requests: int = 0
    total_responses: int = 0
    request_encodings: Dict[str, int] = field(default_factory=dict)
    response_encodings: Dict[str, int] = field(default_factory=dict)
    unknown_encodings: List[str] = field(default_factory=list)

    def display(self) -> str:
        lines = [
            f"Requests analysed : {self.total_requests}",
            f"Responses analysed: {self.total_responses}",
        ]
        if self.request_encodings:
            lines.append("Request encodings:")
            for enc, cnt in sorted(self.request_encodings.items(), key=lambda x: -x[1]):
                lines.append(f"  {enc}: {cnt}")
        if self.response_encodings:
            lines.append("Response encodings:")
            for enc, cnt in sorted(self.response_encodings.items(), key=lambda x: -x[1]):
                lines.append(f"  {enc}: {cnt}")
        if self.unknown_encodings:
            lines.append("Unknown encodings: " + ", ".join(sorted(set(self.unknown_encodings))))
        return "\n".join(lines)


def _extract_encoding(headers: Dict[str, str], key: str) -> Optional[str]:
    for k, v in headers.items():
        if k.lower() == key.lower():
            return v.strip().lower()
    return None


def analyze_encodings(
    requests: List[CapturedRequest],
    responses: List[Optional[CapturedResponse]],
) -> EncodingStats:
    req_counter: Counter = Counter()
    resp_counter: Counter = Counter()
    unknown: List[str] = []

    for req in requests:
        enc = _extract_encoding(req.headers, "content-encoding") or \
              _extract_encoding(req.headers, "transfer-encoding")
        if enc:
            req_counter[enc] += 1
            if enc not in COMMON_ENCODINGS:
                unknown.append(enc)

    for resp in responses:
        if resp is None:
            continue
        enc = _extract_encoding(resp.headers, "content-encoding") or \
              _extract_encoding(resp.headers, "transfer-encoding")
        if enc:
            resp_counter[enc] += 1
            if enc not in COMMON_ENCODINGS:
                unknown.append(enc)

    return EncodingStats(
        total_requests=len(requests),
        total_responses=sum(1 for r in responses if r is not None),
        request_encodings=dict(req_counter),
        response_encodings=dict(resp_counter),
        unknown_encodings=unknown,
    )
