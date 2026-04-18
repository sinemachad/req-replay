"""Tests for req_replay.trace."""
from __future__ import annotations

import pytest

from req_replay.trace import (
    RequestTrace,
    TraceSpan,
    build_trace,
    record_span,
)


def _span_dict(**kwargs) -> dict:
    base = {
        "name": "dns",
        "started_at": "2024-01-01T00:00:00+00:00",
        "ended_at": "2024-01-01T00:00:00+00:00",
        "duration_ms": 12.5,
        "metadata": {},
    }
    base.update(kwargs)
    return base


def test_span_roundtrip():
    d = _span_dict(name="connect", duration_ms=5.0, metadata={"host": "example.com"})
    span = TraceSpan.from_dict(d)
    assert span.name == "connect"
    assert span.duration_ms == 5.0
    assert span.metadata == {"host": "example.com"}
    assert span.to_dict() == d


def test_record_span_appends():
    trace = RequestTrace(request_id="abc")
    span = record_span(trace, "tls", 8.3, {"version": "TLSv1.3"})
    assert len(trace.spans) == 1
    assert trace.spans[0] is span
    assert span.name == "tls"


def test_total_duration_sums_spans():
    trace = RequestTrace(request_id="abc")
    record_span(trace, "dns", 10.0)
    record_span(trace, "connect", 20.0)
    record_span(trace, "tls", 5.0)
    assert trace.total_duration_ms == pytest.approx(35.0)


def test_empty_trace_duration_is_zero():
    trace = RequestTrace(request_id="xyz")
    assert trace.total_duration_ms == 0.0


def test_build_trace_from_dicts():
    spans = [
        _span_dict(name="dns", duration_ms=3.0),
        _span_dict(name="send", duration_ms=7.0),
    ]
    trace = build_trace("req-1", spans)
    assert trace.request_id == "req-1"
    assert len(trace.spans) == 2
    assert trace.spans[0].name == "dns"


def test_display_contains_span_names():
    trace = RequestTrace(request_id="req-99")
    record_span(trace, "dns", 4.0)
    record_span(trace, "tls", 11.5)
    out = trace.display()
    assert "dns" in out
    assert "tls" in out
    assert "15.50" in out


def test_display_contains_request_id():
    trace = RequestTrace(request_id="my-id")
    assert "my-id" in trace.display()


def test_build_trace_empty_spans():
    trace = build_trace("empty", [])
    assert trace.spans == []
    assert trace.total_duration_ms == 0.0
