"""Coerce header values to canonical types (string normalisation)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from req_replay.models import CapturedRequest

# Headers whose values should be lowercased
_LOWERCASE_VALUE_HEADERS = {
    "content-type",
    "accept",
    "accept-encoding",
    "accept-language",
    "transfer-encoding",
    "connection",
}

# Headers whose values should be title-cased (e.g. "keep-alive" -> "Keep-Alive")
_TITLE_VALUE_HEADERS: set[str] = set()


@dataclass
class CoerceChange:
    header: str
    original: str
    coerced: str

    def to_dict(self) -> dict:
        return {
            "header": self.header,
            "original": self.original,
            "coerced": self.coerced,
        }


@dataclass
class CoerceResult:
    headers: Dict[str, str]
    changes: List[CoerceChange] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return len(self.changes) > 0

    def display(self) -> str:
        if not self.changed:
            return "No coercions applied."
        lines = ["Coercions applied:"]
        for c in self.changes:
            lines.append(f"  {c.header}: {c.original!r} -> {c.coerced!r}")
        return "\n".join(lines)


def coerce_headers(headers: Dict[str, str]) -> CoerceResult:
    """Apply value coercions to a header dict and return a CoerceResult."""
    result: Dict[str, str] = {}
    changes: List[CoerceChange] = []

    for key, value in headers.items():
        norm_key = key.lower().strip()
        stripped = value.strip()

        if norm_key in _LOWERCASE_VALUE_HEADERS:
            coerced = stripped.lower()
        elif norm_key in _TITLE_VALUE_HEADERS:
            coerced = stripped.title()
        else:
            coerced = stripped

        if coerced != value:
            changes.append(CoerceChange(header=norm_key, original=value, coerced=coerced))

        result[key] = coerced

    return CoerceResult(headers=result, changes=changes)


def coerce_request_headers(request: CapturedRequest) -> Tuple[CapturedRequest, CoerceResult]:
    """Return a new CapturedRequest with coerced headers and the CoerceResult."""
    coerce_result = coerce_headers(request.headers)
    updated = CapturedRequest(
        id=request.id,
        method=request.method,
        url=request.url,
        headers=coerce_result.headers,
        body=request.body,
        timestamp=request.timestamp,
        tags=list(request.tags),
        metadata=dict(request.metadata),
    )
    return updated, coerce_result
