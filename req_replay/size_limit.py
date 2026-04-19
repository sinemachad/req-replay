"""Warn about requests or responses that exceed configurable size thresholds."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from req_replay.models import CapturedRequest, CapturedResponse


@dataclass
class SizeLimitWarning:
    request_id: str
    kind: str          # 'request' or 'response'
    field: str         # 'body', 'headers'
    actual_bytes: int
    limit_bytes: int

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "kind": self.kind,
            "field": self.field,
            "actual_bytes": self.actual_bytes,
            "limit_bytes": self.limit_bytes,
        }


@dataclass
class SizeLimitResult:
    request_id: str
    warnings: List[SizeLimitWarning] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.warnings) == 0

    def summary(self) -> str:
        if self.passed:
            return f"{self.request_id}: OK"
        parts = [f"{w.kind}/{w.field} {w.actual_bytes}B > {w.limit_bytes}B" for w in self.warnings]
        return f"{self.request_id}: WARN " + ", ".join(parts)


def _header_bytes(headers: dict) -> int:
    return sum(len(k) + len(v) + 4 for k, v in headers.items())


def _body_bytes(body: Optional[str]) -> int:
    if not body:
        return 0
    return len(body.encode("utf-8"))


def check_size_limits(
    request_id: str,
    req: CapturedRequest,
    resp: Optional[CapturedResponse] = None,
    max_request_body: int = 1_048_576,
    max_response_body: int = 5_242_880,
    max_headers: int = 8_192,
) -> SizeLimitResult:
    warnings: List[SizeLimitWarning] = []

    req_body_size = _body_bytes(req.body)
    if req_body_size > max_request_body:
        warnings.append(SizeLimitWarning(request_id, "request", "body", req_body_size, max_request_body))

    req_header_size = _header_bytes(req.headers)
    if req_header_size > max_headers:
        warnings.append(SizeLimitWarning(request_id, "request", "headers", req_header_size, max_headers))

    if resp is not None:
        resp_body_size = _body_bytes(resp.body)
        if resp_body_size > max_response_body:
            warnings.append(SizeLimitWarning(request_id, "response", "body", resp_body_size, max_response_body))

        resp_header_size = _header_bytes(resp.headers)
        if resp_header_size > max_headers:
            warnings.append(SizeLimitWarning(request_id, "response", "headers", resp_header_size, max_headers))

    return SizeLimitResult(request_id=request_id, warnings=warnings)


def scan_size_limits(
    pairs: List[Tuple[CapturedRequest, Optional[CapturedResponse]]],
    **kwargs,
) -> List[SizeLimitResult]:
    results = []
    for req, resp in pairs:
        rid = getattr(req, "id", "unknown")
        results.append(check_size_limits(rid, req, resp, **kwargs))
    return results
