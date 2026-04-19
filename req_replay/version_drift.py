"""Detect API version drift across captured requests."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from req_replay.models import CapturedRequest

_VERSION_PATTERNS = [
    re.compile(r"/v(\d+)/"),
    re.compile(r"[?&]version=(\d+)"),
    re.compile(r"[?&]api_version=([\w.]+)"),
]

_HEADER_NAMES = ["api-version", "x-api-version", "accept-version"]


def _extract_version(req: CapturedRequest) -> Optional[str]:
    for pattern in _VERSION_PATTERNS:
        m = pattern.search(req.url)
        if m:
            return m.group(1)
    lower = {k.lower(): v for k, v in req.headers.items()}
    for h in _HEADER_NAMES:
        if h in lower:
            return lower[h]
    return None


@dataclass
class DriftWarning:
    request_id: str
    url: str
    detected_version: Optional[str]
    expected_version: str
    message: str

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "url": self.url,
            "detected_version": self.detected_version,
            "expected_version": self.expected_version,
            "message": self.message,
        }


@dataclass
class DriftResult:
    warnings: List[DriftWarning] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.warnings) == 0

    def summary(self) -> str:
        if self.passed:
            return "No version drift detected."
        lines = [f"Version drift detected ({len(self.warnings)} warning(s)):"]
        for w in self.warnings:
            lines.append(f"  [{w.request_id}] {w.message}")
        return "\n".join(lines)


def analyze_version_drift(
    requests: List[CapturedRequest],
    expected_version: str,
) -> DriftResult:
    """Check every request uses the expected API version."""
    warnings: List[DriftWarning] = []
    for req in requests:
        detected = _extract_version(req)
        if detected is None:
            warnings.append(
                DriftWarning(
                    request_id=req.id,
                    url=req.url,
                    detected_version=None,
                    expected_version=expected_version,
                    message=f"No API version found in request to {req.url}",
                )
            )
        elif str(detected) != str(expected_version):
            warnings.append(
                DriftWarning(
                    request_id=req.id,
                    url=req.url,
                    detected_version=detected,
                    expected_version=expected_version,
                    message=(
                        f"Version mismatch: got '{detected}', "
                        f"expected '{expected_version}' in {req.url}"
                    ),
                )
            )
    return DriftResult(warnings=warnings)
