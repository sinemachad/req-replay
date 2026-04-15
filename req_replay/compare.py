"""Side-by-side comparison of two stored requests and their responses."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.diff import diff_responses, DiffResult


@dataclass
class CompareResult:
    request_a_id: str
    request_b_id: str
    url_match: bool
    method_match: bool
    headers_only_in_a: dict
    headers_only_in_b: dict
    shared_headers_match: bool
    body_match: bool
    response_diff: Optional[DiffResult] = None

    @property
    def requests_equivalent(self) -> bool:
        return (
            self.url_match
            and self.method_match
            and not self.headers_only_in_a
            and not self.headers_only_in_b
            and self.shared_headers_match
            and self.body_match
        )

    def summary(self) -> str:
        lines = [
            f"Compare {self.request_a_id!r} vs {self.request_b_id!r}",
            f"  URL match          : {self.url_match}",
            f"  Method match       : {self.method_match}",
            f"  Headers only in A  : {list(self.headers_only_in_a)}",
            f"  Headers only in B  : {list(self.headers_only_in_b)}",
            f"  Shared headers ok  : {self.shared_headers_match}",
            f"  Body match         : {self.body_match}",
        ]
        if self.response_diff is not None:
            lines.append(f"  Response diff      : {self.response_diff.summary()}") 
        return "\n".join(lines)


def compare_requests(
    req_a: CapturedRequest,
    req_b: CapturedRequest,
    resp_a: Optional[CapturedResponse] = None,
    resp_b: Optional[CapturedResponse] = None,
) -> CompareResult:
    """Compare two captured requests (and optionally their responses)."""
    url_match = req_a.url == req_b.url
    method_match = req_a.method.upper() == req_b.method.upper()

    keys_a = set(req_a.headers)
    keys_b = set(req_b.headers)
    only_a = {k: req_a.headers[k] for k in keys_a - keys_b}
    only_b = {k: req_b.headers[k] for k in keys_b - keys_a}
    shared_match = all(
        req_a.headers[k] == req_b.headers[k] for k in keys_a & keys_b
    )
    body_match = req_a.body == req_b.body

    response_diff: Optional[DiffResult] = None
    if resp_a is not None and resp_b is not None:
        response_diff = diff_responses(resp_a, resp_b)

    return CompareResult(
        request_a_id=req_a.id,
        request_b_id=req_b.id,
        url_match=url_match,
        method_match=method_match,
        headers_only_in_a=only_a,
        headers_only_in_b=only_b,
        shared_headers_match=shared_match,
        body_match=body_match,
        response_diff=response_diff,
    )
