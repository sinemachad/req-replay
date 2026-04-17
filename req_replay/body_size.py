"""Analyse request/response body sizes across stored requests."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from req_replay.models import CapturedRequest, CapturedResponse


@dataclass
class BodySizeStats:
    count: int
    total_bytes: int
    min_bytes: Optional[int]
    max_bytes: Optional[int]
    mean_bytes: Optional[float]

    def display(self) -> str:
        if self.count == 0 or self.min_bytes is None:
            return "No body data available."
        return (
            f"Samples : {self.count}\n"
            f"Total   : {self.total_bytes} B\n"
            f"Min     : {self.min_bytes} B\n"
            f"Max     : {self.max_bytes} B\n"
            f"Mean    : {self.mean_bytes:.1f} B"
        )


def _body_len(body: Optional[str]) -> Optional[int]:
    if body is None:
        return None
    return len(body.encode())


def analyze_request_sizes(
    requests: List[CapturedRequest],
) -> BodySizeStats:
    sizes = [_body_len(r.body) for r in requests if _body_len(r.body) is not None]
    return _build_stats(sizes)


def analyze_response_sizes(
    pairs: List[Tuple[CapturedRequest, CapturedResponse]],
) -> BodySizeStats:
    sizes = [_body_len(resp.body) for _, resp in pairs if _body_len(resp.body) is not None]
    return _build_stats(sizes)


def _build_stats(sizes: List[int]) -> BodySizeStats:
    if not sizes:
        return BodySizeStats(count=0, total_bytes=0, min_bytes=None, max_bytes=None, mean_bytes=None)
    return BodySizeStats(
        count=len(sizes),
        total_bytes=sum(sizes),
        min_bytes=min(sizes),
        max_bytes=max(sizes),
        mean_bytes=sum(sizes) / len(sizes),
    )
