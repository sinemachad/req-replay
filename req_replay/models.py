"""Data models for HTTP request and response capture."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional
import uuid


@dataclass
class CapturedRequest:
    """Represents a captured HTTP request."""

    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    query_params: Dict[str, str] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    captured_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "method": self.method,
            "url": self.url,
            "headers": self.headers,
            "body": self.body,
            "query_params": self.query_params,
            "captured_at": self.captured_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CapturedRequest":
        return cls(
            id=data["id"],
            method=data["method"],
            url=data["url"],
            headers=data.get("headers", {}),
            body=data.get("body"),
            query_params=data.get("query_params", {}),
            captured_at=data.get("captured_at", datetime.utcnow().isoformat()),
        )


@dataclass
class CapturedResponse:
    """Represents a captured HTTP response."""

    status_code: int
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    request_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "status_code": self.status_code,
            "headers": self.headers,
            "body": self.body,
            "request_id": self.request_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CapturedResponse":
        return cls(
            status_code=data["status_code"],
            headers=data.get("headers", {}),
            body=data.get("body"),
            request_id=data.get("request_id"),
        )
