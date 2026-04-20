"""Header policy enforcement — flag requests that violate expected header rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from req_replay.models import CapturedRequest


@dataclass
class HeaderPolicyWarning:
    code: str
    message: str
    header: str

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "header": self.header}


@dataclass
class HeaderPolicyResult:
    request_id: str
    warnings: List[HeaderPolicyWarning] = field(default_factory=list)

    def passed(self) -> bool:
        return len(self.warnings) == 0

    def summary(self) -> str:
        if self.passed():
            return f"{self.request_id}: OK"
        codes = ", ".join(w.code for w in self.warnings)
        return f"{self.request_id}: {len(self.warnings)} warning(s) [{codes}]"

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "passed": self.passed(),
            "warnings": [w.to_dict() for w in self.warnings],
        }


# Required headers that every request should carry
_REQUIRED_HEADERS = ["user-agent", "accept"]
# Headers that must NOT appear in outbound requests (security hygiene)
_FORBIDDEN_HEADERS = ["x-internal-secret", "x-debug-token"]


def check_header_policy(
    request: CapturedRequest,
    required: Optional[List[str]] = None,
    forbidden: Optional[List[str]] = None,
) -> HeaderPolicyResult:
    """Evaluate *request* against header policy rules.

    Args:
        request: The captured request to evaluate.
        required: Header names (lower-case) that must be present.  Defaults to
            ``_REQUIRED_HEADERS``.
        forbidden: Header names (lower-case) that must be absent.  Defaults to
            ``_FORBIDDEN_HEADERS``.

    Returns:
        A :class:`HeaderPolicyResult` with any policy violations.
    """
    required = required if required is not None else _REQUIRED_HEADERS
    forbidden = forbidden if forbidden is not None else _FORBIDDEN_HEADERS

    present = {k.lower() for k in (request.headers or {})}
    warnings: List[HeaderPolicyWarning] = []

    for hdr in required:
        if hdr not in present:
            warnings.append(
                HeaderPolicyWarning(
                    code="HP001",
                    message=f"Required header '{hdr}' is missing",
                    header=hdr,
                )
            )

    for hdr in forbidden:
        if hdr in present:
            warnings.append(
                HeaderPolicyWarning(
                    code="HP002",
                    message=f"Forbidden header '{hdr}' is present",
                    header=hdr,
                )
            )

    return HeaderPolicyResult(request_id=request.id, warnings=warnings)


def scan_header_policy(
    requests: List[CapturedRequest],
    required: Optional[List[str]] = None,
    forbidden: Optional[List[str]] = None,
) -> List[HeaderPolicyResult]:
    """Run :func:`check_header_policy` over a list of requests."""
    return [check_header_policy(r, required=required, forbidden=forbidden) for r in requests]
