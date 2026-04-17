"""Utilities for detecting and summarising authentication schemes used in captured requests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional

from req_replay.models import CapturedRequest


@dataclass
class AuthSummary:
    scheme: str          # e.g. "Bearer", "Basic", "ApiKey", "None"
    header: str          # header that carried the credential
    masked_value: str    # partially redacted value for display

    def display(self) -> str:
        return f"{self.header}: [{self.scheme}] {self.masked_value}"


def _mask(value: str, keep: int = 6) -> str:
    """Return value with all but the first *keep* chars replaced by '*'."""
    if len(value) <= keep:
        return "*" * len(value)
    return value[:keep] + "*" * (len(value) - keep)


def detect_auth(request: CapturedRequest) -> Optional[AuthSummary]:
    """Inspect *request* headers and return an AuthSummary if a credential is found."""
    lower_headers: Dict[str, str] = {k.lower(): k for k in request.headers}

    # Authorization header — Bearer / Basic / other
    if "authorization" in lower_headers:
        original_key = lower_headers["authorization"]
        raw = request.headers[original_key]
        parts = raw.split(" ", 1)
        scheme = parts[0] if len(parts) == 2 else "Unknown"
        credential = parts[1] if len(parts) == 2 else raw
        return AuthSummary(
            scheme=scheme,
            header=original_key,
            masked_value=_mask(credential),
        )

    # Common API-key header names
    api_key_headers = {"x-api-key", "api-key", "x-auth-token"}
    for lower_key, original_key in lower_headers.items():
        if lower_key in api_key_headers:
            return AuthSummary(
                scheme="ApiKey",
                header=original_key,
                masked_value=_mask(request.headers[original_key]),
            )

    return None


def analyze_auth(requests: List[CapturedRequest]) -> Dict[str, int]:
    """Return a frequency map of auth schemes across *requests*."""
    counts: Dict[str, int] = {}
    for req in requests:
        summary = detect_auth(req)
        scheme = summary.scheme if summary else "None"
        counts[scheme] = counts.get(scheme, 0) + 1
    return counts
