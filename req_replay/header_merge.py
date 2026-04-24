"""Merge headers from multiple requests into a unified header map."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from req_replay.models import CapturedRequest


@dataclass
class MergeResult:
    merged: Dict[str, str]
    conflicts: Dict[str, List[str]]  # key -> list of differing values
    sources: int

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)

    def display(self) -> str:
        lines = [f"Merged {self.sources} request(s), {len(self.merged)} header(s)"]
        if self.conflicts:
            lines.append(f"Conflicts ({len(self.conflicts)}):")
            for key, values in sorted(self.conflicts.items()):
                lines.append(f"  {key}: " + " | ".join(values))
        else:
            lines.append("No conflicts.")
        return "\n".join(lines)


def merge_headers(
    requests: List[CapturedRequest],
    strategy: str = "first",
    extra: Optional[Dict[str, str]] = None,
) -> MergeResult:
    """Merge headers from *requests*.

    strategy:
        'first'  – keep the first seen value for each key (default)
        'last'   – keep the last seen value
        'union'  – raise conflict for differing values
    """
    if strategy not in ("first", "last", "union"):
        raise ValueError(f"Unknown strategy: {strategy!r}")

    merged: Dict[str, str] = {}
    conflicts: Dict[str, List[str]] = {}

    for req in requests:
        for raw_key, value in (req.headers or {}).items():
            key = raw_key.lower()
            if key not in merged:
                merged[key] = value
            else:
                existing = merged[key]
                if existing != value:
                    if strategy == "last":
                        merged[key] = value
                    if strategy in ("last", "union"):
                        bucket = conflicts.setdefault(key, [existing])
                        if value not in bucket:
                            bucket.append(value)

    if extra:
        for raw_key, value in extra.items():
            merged[raw_key.lower()] = value

    return MergeResult(merged=merged, conflicts=conflicts, sources=len(requests))
