"""Header diff: compare headers between two captured requests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from req_replay.models import CapturedRequest


@dataclass
class HeaderDiffWarning:
    code: str
    message: str

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message}


@dataclass
class HeaderDiffResult:
    request_id_a: str
    request_id_b: str
    added: Dict[str, str] = field(default_factory=dict)      # in B, not in A
    removed: Dict[str, str] = field(default_factory=dict)    # in A, not in B
    changed: Dict[str, tuple] = field(default_factory=dict)  # key -> (val_a, val_b)
    warnings: List[HeaderDiffWarning] = field(default_factory=list)

    @property
    def identical(self) -> bool:
        return not (self.added or self.removed or self.changed)

    def summary(self) -> str:
        if self.identical:
            return "Headers are identical."
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.changed:
            parts.append(f"~{len(self.changed)} changed")
        return "Header diff: " + ", ".join(parts) + "."


def _normalise(headers: Dict[str, str]) -> Dict[str, str]:
    """Return headers with lower-cased keys."""
    return {k.lower(): v for k, v in (headers or {}).items()}


def diff_headers(
    req_a: CapturedRequest,
    req_b: CapturedRequest,
    ignore: Optional[Set[str]] = None,
) -> HeaderDiffResult:
    """Compare headers of two requests and return a HeaderDiffResult."""
    ignore_keys: Set[str] = {k.lower() for k in (ignore or set())}

    norm_a = {k: v for k, v in _normalise(req_a.headers).items() if k not in ignore_keys}
    norm_b = {k: v for k, v in _normalise(req_b.headers).items() if k not in ignore_keys}

    keys_a: Set[str] = set(norm_a)
    keys_b: Set[str] = set(norm_b)

    added = {k: norm_b[k] for k in keys_b - keys_a}
    removed = {k: norm_a[k] for k in keys_a - keys_b}
    changed = {
        k: (norm_a[k], norm_b[k])
        for k in keys_a & keys_b
        if norm_a[k] != norm_b[k]
    }

    warnings: List[HeaderDiffWarning] = []
    if "authorization" in added or "authorization" in changed:
        warnings.append(
            HeaderDiffWarning(
                code="HD001",
                message="Authorization header differs between requests.",
            )
        )
    if "content-type" in changed:
        warnings.append(
            HeaderDiffWarning(
                code="HD002",
                message="Content-Type header differs between requests.",
            )
        )

    return HeaderDiffResult(
        request_id_a=req_a.id,
        request_id_b=req_b.id,
        added=added,
        removed=removed,
        changed=changed,
        warnings=warnings,
    )
