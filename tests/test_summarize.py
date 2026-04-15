"""Tests for req_replay.summarize."""
import pytest

from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.summarize import RequestSummary, summarize


def _req(method="GET", url="https://example.com/api") -> CapturedRequest:
    return CapturedRequest(
        id="test-id",
        method=method,
        url=url,
        headers={},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
    )


def _resp(status: int = 200, body: str = "") -> CapturedResponse:
    return CapturedResponse(status_code=status, headers={}, body=body, elapsed_ms=10.0)


def test_empty_pairs_returns_zero_summary():
    result = summarize([])
    assert result.total == 0
    assert result.by_method == {}
    assert result.error_rate == 0.0


def test_total_count():
    pairs = [(_req(), _resp()), (_req(), _resp())]
    result = summarize(pairs)
    assert result.total == 2


def test_by_method_counts():
    pairs = [
        (_req(method="GET"), _resp()),
        (_req(method="POST"), _resp()),
        (_req(method="get"), _resp()),  # case normalised
    ]
    result = summarize(pairs)
    assert result.by_method["GET"] == 2
    assert result.by_method["POST"] == 1


def test_by_status_counts():
    pairs = [
        (_req(), _resp(200)),
        (_req(), _resp(200)),
        (_req(), _resp(404)),
    ]
    result = summarize(pairs)
    assert result.by_status[200] == 2
    assert result.by_status[404] == 1


def test_by_host_counts():
    pairs = [
        (_req(url="https://alpha.com/x"), _resp()),
        (_req(url="https://alpha.com/y"), _resp()),
        (_req(url="https://beta.com/z"), _resp()),
    ]
    result = summarize(pairs)
    assert result.by_host["alpha.com"] == 2
    assert result.by_host["beta.com"] == 1


def test_error_rate_all_errors():
    pairs = [(_req(), _resp(500)), (_req(), _resp(503))]
    result = summarize(pairs)
    assert result.error_rate == pytest.approx(1.0)


def test_error_rate_no_errors():
    pairs = [(_req(), _resp(200)), (_req(), _resp(201))]
    result = summarize(pairs)
    assert result.error_rate == pytest.approx(0.0)


def test_error_rate_partial():
    pairs = [(_req(), _resp(200)), (_req(), _resp(500))]
    result = summarize(pairs)
    assert result.error_rate == pytest.approx(0.5)


def test_avg_response_size():
    body = "hello"  # 5 bytes
    pairs = [(_req(), _resp(200, body)), (_req(), _resp(200, body))]
    result = summarize(pairs)
    assert result.avg_response_size_bytes == pytest.approx(5.0)


def test_none_response_excluded_from_stats():
    pairs = [(_req(), None), (_req(), _resp(200))]
    result = summarize(pairs)
    assert result.total == 2
    assert result.by_status.get(200) == 1
    assert result.error_rate == pytest.approx(0.0)


def test_display_returns_string():
    pairs = [(_req(), _resp(200, "ok"))]
    result = summarize(pairs)
    text = result.display()
    assert "Total requests" in text
    assert "Error rate" in text
