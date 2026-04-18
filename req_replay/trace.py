"""Request trace — attach structured trace spans to a captured request."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class TraceSpan:
    name: str
    started_at: str
    ended_at: str
    duration_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TraceSpan":
        return cls(
            name=d["name"],
            started_at=d["started_at"],
            ended_at=d["ended_at"],
            duration_ms=d["duration_ms"],
            metadata=d.get("metadata", {}),
        )


@dataclass
class RequestTrace:
    request_id: str
    spans: list[TraceSpan] = field(default_factory=list)

    @property
    def total_duration_ms(self) -> float:
        return sum(s.duration_ms for s in self.spans)

    def display(self) -> str:
        lines = [f"Trace for request {self.request_id}"]
        for s in self.spans:
            lines.append(f"  [{s.name}] {s.duration_ms:.2f} ms")
        lines.append(f"  Total: {self.total_duration_ms:.2f} ms")
        return "\n".join(lines)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_span(
    trace: RequestTrace,
    name: str,
    duration_ms: float,
    metadata: dict[str, Any] | None = None,
) -> TraceSpan:
    """Append a new span to *trace* and return it."""
    now = _now_iso()
    span = TraceSpan(
        name=name,
        started_at=now,
        ended_at=now,
        duration_ms=duration_ms,
        metadata=metadata or {},
    )
    trace.spans.append(span)
    return span


def build_trace(request_id: str, spans: list[dict]) -> RequestTrace:
    """Construct a RequestTrace from a list of raw span dicts."""
    return RequestTrace(
        request_id=request_id,
        spans=[TraceSpan.from_dict(s) for s in spans],
    )
