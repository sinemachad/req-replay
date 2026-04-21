"""Header injection: add or override headers on stored requests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from req_replay.models import CapturedRequest


@dataclass
class InjectionResult:
    request_id: str
    added: List[str] = field(default_factory=list)
    overridden: List[str] = field(default_factory=list)
    original_headers: Dict[str, str] = field(default_factory=dict)
    updated_headers: Dict[str, str] = field(default_factory=dict)

    @property
    def changed(self) -> bool:
        return bool(self.added or self.overridden)

    def display(self) -> str:
        lines = [f"Request: {self.request_id}"]
        if self.added:
            lines.append("  Added:    " + ", ".join(self.added))
        if self.overridden:
            lines.append("  Overridden: " + ", ".join(self.overridden))
        if not self.changed:
            lines.append("  No changes.")
        return "\n".join(lines)


def inject_headers(
    request: CapturedRequest,
    headers: Dict[str, str],
    *,
    overwrite: bool = True,
) -> tuple[CapturedRequest, InjectionResult]:
    """Return a new CapturedRequest with *headers* injected.

    Args:
        request:   The original captured request.
        headers:   Mapping of header name -> value to inject.
        overwrite: When True (default) existing headers are replaced;
                   when False existing headers are left untouched.

    Returns:
        A (new_request, InjectionResult) tuple.
    """
    original = {k.lower(): v for k, v in (request.headers or {}).items()}
    merged = dict(original)
    added: List[str] = []
    overridden: List[str] = []

    for key, value in headers.items():
        norm = key.lower()
        if norm in merged:
            if overwrite:
                overridden.append(norm)
                merged[norm] = value
        else:
            added.append(norm)
            merged[norm] = value

    import dataclasses
    new_request = dataclasses.replace(request, headers=merged)

    result = InjectionResult(
        request_id=request.id,
        added=sorted(added),
        overridden=sorted(overridden),
        original_headers=original,
        updated_headers=merged,
    )
    return new_request, result
