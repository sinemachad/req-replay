"""Tests for req_replay.severity."""
import pytest
from req_replay.severity import (
    classify,
    analyze_severity,
    severity_summary,
    SeverityResult,
    LEVEL_OK,
    LEVEL_WARNING,
    LEVEL_ERROR,
    LEVEL_CRITICAL,
)
from req_replay.models import CapturedRequest, CapturedResponse
from datetime import datetime


def _req(rid: str = "req-1") -> CapturedRequest:
    return CapturedRequest(
        id=rid,
        method="GET",
        url="https://example.com/api",
        headers={},
        body=None,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        tags=[],
        metadata={},
    )


def _resp(status: int) -> CapturedResponse:
    return CapturedResponse(
        status_code=status,
        headers={},
        body=None,
    )


def test_classify_200_is_ok():
    level, reason = classify(200)
    assert level == LEVEL_OK


def test_classify_201_is_ok():
    level, _ = classify(201)
    assert level == LEVEL_OK


def test_classify_401_is_warning():
    level, reason = classify(401)
    assert level == LEVEL_WARNING
    assert "Unauthorized" in reason


def test_classify_404_is_warning():
    level, _ = classify(404)
    assert level == LEVEL_WARNING


def test_classify_400_is_error():
    level, _ = classify(400)
    assert level == LEVEL_ERROR


def test_classify_422_is_error():
    level, _ = classify(422)
    assert level == LEVEL_ERROR


def test_classify_500_is_critical():
    level, reason = classify(500)
    assert level == LEVEL_CRITICAL
    assert "500" in reason


def test_analyze_severity_returns_results():
    pairs = [(_req("a"), _resp(200)), (_req("b"), _resp(500))]
    results = analyze_severity(pairs)
    assert len(results) == 2
    assert results[0].level == LEVEL_OK
    assert results[1].level == LEVEL_CRITICAL


def test_analyze_severity_empty():
    assert analyze_severity([]) == []


def test_severity_result_to_dict():
    r = SeverityResult(request_id="x", status_code=404, level=LEVEL_WARNING, reason="Not Found")
    d = r.to_dict()
    assert d["request_id"] == "x"
    assert d["level"] == LEVEL_WARNING


def test_severity_result_display():
    r = SeverityResult(request_id="x", status_code=500, level=LEVEL_CRITICAL, reason="Server error")
    assert "CRITICAL" in r.display()
    assert "500" in r.display()


def test_severity_summary_counts():
    pairs = [
        (_req("a"), _resp(200)),
        (_req("b"), _resp(404)),
        (_req("c"), _resp(500)),
        (_req("d"), _resp(503)),
    ]
    results = analyze_severity(pairs)
    summary = severity_summary(results)
    assert "Total: 4" in summary
    assert "Critical: 2" in summary
