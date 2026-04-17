"""Tests for req_replay.status."""
from __future__ import annotations

from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.status import StatusStats, _class_label, analyze_status

import pytest
from datetime import datetime


def _req() -> CapturedRequest:
    return CapturedRequest(
        id="r1",
        method="GET",
        url="http://example.com",
        headers={},
        body="",
        timestamp=datetime(2024, 1, 1),
    )


def _resp(code: int) -> CapturedResponse:
    return CapturedResponse(status_code=code, headers={}, body="", elapsed_ms=10.0)


def test_empty_pairs_returns_zero_stats():
    stats = analyze_status([])
    assert stats.total == 0
    assert stats.by_code == {}
    assert stats.by_class == {}


def test_single_200_response():
    stats = analyze_status([(_req(), _resp(200))])
    assert stats.total == 1
    assert stats.by_code == {200: 1}
    assert stats.by_class == {"2xx success": 1}


def test_multiple_responses_counted():
    pairs = [(_req(), _resp(200)), (_req(), _resp(200)), (_req(), _resp(404))]
    stats = analyze_status(pairs)
    assert stats.total == 3
    assert stats.by_code[200] == 2
    assert stats.by_code[404] == 1


def test_class_grouping():
    pairs = [(_req(), _resp(201)), (_req(), _resp(400)), (_req(), _resp(500))]
    stats = analyze_status(pairs)
    assert stats.by_class["2xx success"] == 1
    assert stats.by_class["4xx client error"] == 1
    assert stats.by_class["5xx server error"] == 1


@pytest.mark.parametrize("code,label", [
    (100, "1xx informational"),
    (200, "2xx success"),
    (301, "3xx redirection"),
    (404, "4xx client error"),
    (503, "5xx server error"),
    (999, "unknown"),
])
def test_class_label(code, label):
    assert _class_label(code) == label


def test_display_empty():
    stats = StatusStats(total=0)
    assert "No responses" in stats.display()


def test_display_non_empty():
    stats = analyze_status([(_req(), _resp(200)), (_req(), _resp(404))])
    out = stats.display()
    assert "200" in out
    assert "404" in out
    assert "2xx success" in out
    assert "4xx client error" in out
