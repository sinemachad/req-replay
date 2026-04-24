"""Detect, filter, and strip headers by prefix."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from req_replay.models import CapturedRequest


@dataclass
class PrefixResult:
    matched: Dict[str, str] = field(default_factory=dict)
    stripped: Dict[str, str] = field(default_factory=dict)
    original_count: int = 0
    final_count: int = 0

    @property
    def changed(self) -> bool:
        return bool(self.stripped)

    def display(self) -> str:
        lines = [
            f"Original headers : {self.original_count}",
            f"Matched prefix   : {len(self.matched)}",
            f"Stripped         : {len(self.stripped)}",
            f"Final headers    : {self.final_count}",
        ]
        if self.stripped:
            lines.append("Removed:")
            for k, v in sorted(self.stripped.items()):
                lines.append(f"  - {k}: {v}")
        return "\n".join(lines)


def find_by_prefix(
    headers: Dict[str, str],
    prefix: str,
    *,
    case_sensitive: bool = False,
) -> Dict[str, str]:
    """Return headers whose keys start with *prefix*."""
    cmp_prefix = prefix if case_sensitive else prefix.lower()
    return {
        k: v
        for k, v in headers.items()
        if (k if case_sensitive else k.lower()).startswith(cmp_prefix)
    }


def strip_by_prefix(
    headers: Dict[str, str],
    prefix: str,
    *,
    case_sensitive: bool = False,
) -> PrefixResult:
    """Strip all headers whose key starts with *prefix*."""
    matched = find_by_prefix(headers, prefix, case_sensitive=case_sensitive)
    remaining = {k: v for k, v in headers.items() if k not in matched}
    return PrefixResult(
        matched=matched,
        stripped=matched,
        original_count=len(headers),
        final_count=len(remaining),
    )


def strip_request_headers_by_prefix(
    request: CapturedRequest,
    prefix: str,
    *,
    case_sensitive: bool = False,
) -> tuple[CapturedRequest, PrefixResult]:
    """Return a new request with matching headers removed plus a PrefixResult."""
    result = strip_by_prefix(request.headers, prefix, case_sensitive=case_sensitive)
    new_headers = {k: v for k, v in request.headers.items() if k not in result.stripped}
    new_request = CapturedRequest(
        id=request.id,
        method=request.method,
        url=request.url,
        headers=new_headers,
        body=request.body,
        timestamp=request.timestamp,
        tags=request.tags,
        metadata=request.metadata,
    )
    return new_request, result
