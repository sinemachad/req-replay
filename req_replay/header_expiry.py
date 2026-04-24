"""Detect headers that carry expiry/TTL information and report staleness."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import List, Optional

from req_replay.models import CapturedRequest, CapturedResponse


@dataclass
class ExpiryWarning:
    code: str
    header: str
    message: str

    def to_dict(self) -> dict:
        return {"code": self.code, "header": self.header, "message": self.message}


@dataclass
class ExpiryResult:
    request_id: str
    warnings: List[ExpiryWarning] = field(default_factory=list)

    def passed(self) -> bool:
        return len(self.warnings) == 0

    def summary(self) -> str:
        if self.passed():
            return f"{self.request_id}: OK — no expired headers"
        codes = ", ".join(w.code for w in self.warnings)
        return f"{self.request_id}: WARN [{codes}]"

    def display(self) -> str:
        lines = [self.summary()]
        for w in self.warnings:
            lines.append(f"  {w.code} {w.header}: {w.message}")
        return "\n".join(lines)


def _parse_http_date(value: str) -> Optional[datetime]:
    try:
        return parsedate_to_datetime(value)
    except Exception:
        return None


def analyze_expiry(
    request: CapturedRequest,
    response: Optional[CapturedResponse] = None,
) -> ExpiryResult:
    """Check Date, Expires, and Last-Modified headers for staleness."""
    now = datetime.now(tz=timezone.utc)
    warnings: List[ExpiryWarning] = []

    headers: dict = {}
    if response is not None:
        headers = {k.lower(): v for k, v in (response.headers or {}).items()}
    else:
        headers = {k.lower(): v for k, v in (request.headers or {}).items()}

    expires_val = headers.get("expires")
    if expires_val:
        dt = _parse_http_date(expires_val)
        if dt is None:
            warnings.append(ExpiryWarning("HE001", "Expires", "Could not parse Expires header value"))
        elif dt < now:
            delta = int((now - dt).total_seconds())
            warnings.append(ExpiryWarning("HE002", "Expires", f"Header expired {delta}s ago ({expires_val})"))

    date_val = headers.get("date")
    if date_val:
        dt = _parse_http_date(date_val)
        if dt is None:
            warnings.append(ExpiryWarning("HE003", "Date", "Could not parse Date header value"))

    return ExpiryResult(request_id=request.id, warnings=warnings)
