"""Strip unwanted headers from captured requests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from req_replay.models import CapturedRequest

# Headers that are commonly stripped before replay or storage
DEFAULT_STRIP_HEADERS: List[str] = [
    "host",
    "content-length",
    "transfer-encoding",
    "connection",
]


@dataclass
class StripResult:
    original_headers: Dict[str, str]
    stripped_headers: Dict[str, str]
    removed: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return len(self.removed) > 0

    def display(self) -> str:
        if not self.changed:
            return "No headers stripped."
        lines = [f"Stripped {len(self.removed)} header(s):"]
        for key in self.removed:
            lines.append(f"  - {key}")
        return "\n".join(lines)


def strip_headers(
    headers: Dict[str, str],
    strip: Optional[List[str]] = None,
    *,
    use_defaults: bool = True,
) -> StripResult:
    """Return a copy of *headers* with unwanted keys removed.

    Args:
        headers: The original header mapping.
        strip: Additional header names to remove (case-insensitive).
        use_defaults: When True, also remove DEFAULT_STRIP_HEADERS.
    """
    targets: List[str] = []
    if use_defaults:
        targets.extend(DEFAULT_STRIP_HEADERS)
    if strip:
        targets.extend(strip)
    normalised_targets = {k.lower() for k in targets}

    removed: List[str] = []
    result: Dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in normalised_targets:
            removed.append(key)
        else:
            result[key] = value

    return StripResult(
        original_headers=dict(headers),
        stripped_headers=result,
        removed=removed,
    )


def strip_request_headers(
    request: CapturedRequest,
    strip: Optional[List[str]] = None,
    *,
    use_defaults: bool = True,
) -> tuple[CapturedRequest, StripResult]:
    """Return a new request with unwanted headers removed, plus a diff result."""
    result = strip_headers(request.headers, strip=strip, use_defaults=use_defaults)
    new_request = CapturedRequest(
        id=request.id,
        method=request.method,
        url=request.url,
        headers=result.stripped_headers,
        body=request.body,
        timestamp=request.timestamp,
        tags=list(request.tags),
        metadata=dict(request.metadata),
    )
    return new_request, result
