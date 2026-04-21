"""Rename headers in captured requests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from req_replay.models import CapturedRequest


@dataclass
class RenameResult:
    original_headers: Dict[str, str]
    renamed_headers: Dict[str, str]
    renames_applied: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return len(self.renames_applied) > 0

    def display(self) -> str:
        if not self.changed:
            return "No headers renamed."
        lines = ["Renamed headers:"]
        for entry in self.renames_applied:
            lines.append(f"  {entry}")
        return "\n".join(lines)


def rename_headers(
    headers: Dict[str, str],
    rename_map: Dict[str, str],
) -> RenameResult:
    """Return a new headers dict with keys renamed according to rename_map.

    Keys in rename_map are matched case-insensitively against existing headers.
    The replacement key is stored exactly as provided in rename_map values.
    If the old and new names are the same (case-insensitively), no rename occurs.
    """
    original = dict(headers)
    result: Dict[str, str] = {}
    applied: List[str] = []

    # Build a lookup: lower(old_name) -> new_name
    lower_map: Dict[str, str] = {k.lower(): v for k, v in rename_map.items()}

    for key, value in headers.items():
        lower_key = key.lower()
        if lower_key in lower_map:
            new_key = lower_map[lower_key]
            if new_key.lower() != lower_key:
                result[new_key] = value
                applied.append(f"{key} -> {new_key}")
                continue
        result[key] = value

    return RenameResult(
        original_headers=original,
        renamed_headers=result,
        renames_applied=applied,
    )


def rename_request_headers(
    request: CapturedRequest,
    rename_map: Dict[str, str],
) -> tuple[CapturedRequest, RenameResult]:
    """Apply header renames to a CapturedRequest and return updated request + result."""
    result = rename_headers(request.headers, rename_map)
    updated = CapturedRequest(
        id=request.id,
        method=request.method,
        url=request.url,
        headers=result.renamed_headers,
        body=request.body,
        timestamp=request.timestamp,
        tags=list(request.tags),
        metadata=dict(request.metadata),
    )
    return updated, result
