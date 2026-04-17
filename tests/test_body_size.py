"""Tests for req_replay.body_size."""
from __future__ import annotations

import pytest

from req_replay.body_size import (
    BodySizeStats,
    _build_stats,
    analyze_request_sizes,
    analyze_response_sizes,
)
from req_replay.models import CapturedRequest, CapturedResponse


def _req(body: str | None = None) -> CapturedRequest:
    return CapturedRequest(
        id="abc",
        method="POST",
        url="http://example.com/api",
        headers={},
        body=body,
        timestamp="2024-01-01T00:00:00",
        tags=[],
    )


def _resp(body: str | None = None) -> CapturedResponse:
    return CapturedResponse(status_code=200, headers={}, body=body)


def test_empty_list_returns_zero_stats():
    stats = analyze_request_sizes([])
    assert stats.count == 0
    assert stats.min_bytes is None


def test_none_bodies_excluded():
    stats = analyze_request_sizes([_req(None), _req(None)])
    assert stats.count == 0


def test_single_request_body():
    stats = analyze_request_sizes([_req('{"a":1}')])
    assert stats.count == 1
    assert stats.min_bytes == stats.max_bytes == stats.total_bytes


def test_multiple_request_bodies():
    reqs = [_req("hi"), _req("hello world")]
    stats = analyze_request_sizes(reqs)
    assert stats.count == 2
    assert stats.min_bytes == 2
    assert stats.max_bytes == 11
    assert stats.mean_bytes == pytest.approx(6.5)


def test_response_sizes_empty():
    stats = analyze_response_sizes([])
    assert stats.count == 0


def test_response_sizes_counted():
    pairs = [(_req(), _resp("ok")), (_req(), _resp("longer body"))]
    stats = analyze_response_sizes(pairs)
    assert stats.count == 2
    assert stats.min_bytes == 2


def test_display_no_data():
    stats = _build_stats([])
    assert "No body" in stats.display()


def test_display_with_data():
    stats = _build_stats([10, 20, 30])
    out = stats.display()
    assert "Min" in out
    assert "Max" in out
    assert "Mean" in out
