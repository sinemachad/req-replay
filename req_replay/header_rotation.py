"""Header rotation: cycle through a list of header values across requests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from req_replay.models import CapturedRequest


@dataclass
class RotationResult:
    request_id: str
    header: str
    old_value: Optional[str]
    new_value: str
    index: int
    changed: bool

    def display(self) -> str:
        status = "changed" if self.changed else "unchanged"
        return (
            f"[{status}] {self.header}: "
            f"{self.old_value!r} -> {self.new_value!r} (slot {self.index})"
        )


@dataclass
class RotationConfig:
    """Maps header names to an ordered list of candidate values."""
    values: Dict[str, List[str]] = field(default_factory=dict)
    _counters: Dict[str, int] = field(default_factory=dict, init=False, repr=False)

    def next_index(self, header: str) -> int:
        """Return the next round-robin index for *header* and advance the counter."""
        key = header.lower()
        pool = self.values.get(key, [])
        if not pool:
            return 0
        idx = self._counters.get(key, 0) % len(pool)
        self._counters[key] = idx + 1
        return idx

    def reset(self, header: Optional[str] = None) -> None:
        """Reset counter(s). Pass *header* to reset a single key, or None for all."""
        if header is None:
            self._counters.clear()
        else:
            self._counters.pop(header.lower(), None)


def rotate_headers(
    request: CapturedRequest,
    config: RotationConfig,
) -> tuple[CapturedRequest, List[RotationResult]]:
    """Return a new request with rotated header values and a list of results."""
    new_headers = dict(request.headers)
    results: List[RotationResult] = []

    for raw_header, pool in config.values.items():
        key = raw_header.lower()
        if not pool:
            continue
        idx = config.next_index(key)
        new_value = pool[idx]
        old_value = new_headers.get(key)
        new_headers[key] = new_value
        results.append(
            RotationResult(
                request_id=request.id,
                header=key,
                old_value=old_value,
                new_value=new_value,
                index=idx,
                changed=old_value != new_value,
            )
        )

    from dataclasses import replace
    new_request = replace(request, headers=new_headers)
    return new_request, results
