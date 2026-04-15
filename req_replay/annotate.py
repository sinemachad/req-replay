"""Annotation support: attach free-form notes to captured requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from req_replay.models import CapturedRequest
from req_replay.storage import RequestStore


@dataclass
class Annotation:
    note: str
    author: Optional[str] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "note": self.note,
            "author": self.author,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Annotation":
        return cls(
            note=data["note"],
            author=data.get("author"),
            created_at=data.get("created_at", ""),
        )


def add_annotation(
    request: CapturedRequest,
    note: str,
    author: Optional[str] = None,
) -> CapturedRequest:
    """Return a new CapturedRequest with the annotation appended."""
    annotation = Annotation(note=note, author=author)
    existing: List[dict] = list(request.metadata.get("annotations", []))
    existing.append(annotation.to_dict())
    new_metadata = {**request.metadata, "annotations": existing}
    return CapturedRequest(
        id=request.id,
        method=request.method,
        url=request.url,
        headers=request.headers,
        body=request.body,
        timestamp=request.timestamp,
        tags=request.tags,
        metadata=new_metadata,
    )


def get_annotations(request: CapturedRequest) -> List[Annotation]:
    """Return all annotations attached to a request."""
    raw = request.metadata.get("annotations", [])
    return [Annotation.from_dict(a) for a in raw]


def clear_annotations(request: CapturedRequest) -> CapturedRequest:
    """Return a new CapturedRequest with all annotations removed."""
    new_metadata = {k: v for k, v in request.metadata.items() if k != "annotations"}
    return CapturedRequest(
        id=request.id,
        method=request.method,
        url=request.url,
        headers=request.headers,
        body=request.body,
        timestamp=request.timestamp,
        tags=request.tags,
        metadata=new_metadata,
    )


def save_annotated(
    store: RequestStore, request: CapturedRequest
) -> None:
    """Persist an annotated request back to the store."""
    store.save(request)
