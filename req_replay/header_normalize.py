"""Normalize HTTP headers across captured requests for consistent comparison."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from req_replay.models import CapturedRequest

# Headers that should be lowercased for canonical comparison
_CANONICAL_LOWER = {
    "content-type",
    "accept",
    "authorization",
    "user-agent",
    "accept-encoding",
    "accept-language",
    "cache-control",
    "connection",
    "host",
}


@dataclass
class NormalizeResult:
    original: Dict[str, str]
    normalized: Dict[str, str]
    changes: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return len(self.changes) > 0

    def display(self) -> str:
        if not self.changed:
            return "Headers already normalized."
        lines = [f"Normalized {len(self.changes)} header(s):"]
        for c in self.changes:
            lines.append(f"  - {c}")
        return "\n".join(lines)


def normalize_headers(
    headers: Dict[str, str],
    lowercase_keys: bool = True,
    strip_values: bool = True,
    remove_empty: bool = True,
    canonical_only: Optional[bool] = False,
) -> NormalizeResult:
    """Return a NormalizeResult with cleaned headers."""
    original = dict(headers)
    normalized: Dict[str, str] = {}
    changes: List[str] = []

    for key, value in headers.items():
        new_key = key.lower() if lowercase_keys else key
        new_value = value.strip() if strip_values else value

        if remove_empty and not new_value:
            changes.append(f"removed empty header '{key}'")
            continue

        if canonical_only and new_key not in _CANONICAL_LOWER:
            changes.append(f"dropped non-canonical header '{key}'")
            continue

        if new_key != key:
            changes.append(f"renamed '{key}' -> '{new_key}'")
        if new_value != value:
            changes.append(f"stripped value for '{new_key}'")

        normalized[new_key] = new_value

    return NormalizeResult(original=original, normalized=normalized, changes=changes)


def normalize_request_headers(
    request: CapturedRequest,
    lowercase_keys: bool = True,
    strip_values: bool = True,
    remove_empty: bool = True,
) -> CapturedRequest:
    """Return a new CapturedRequest with normalized headers."""
    result = normalize_headers(
        request.headers,
        lowercase_keys=lowercase_keys,
        strip_values=strip_values,
        remove_empty=remove_empty,
    )
    import copy
    new_req = copy.deepcopy(request)
    new_req.headers = result.normalized
    return new_req
