"""Tests for req_replay.size_limit."""
import pytest
from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.size_limit import check_size_limits, scan_size_limits


def _req(body: str = "", headers: dict | None = None) -> CapturedRequest:
    return CapturedRequest(
        id="req-1",
        method="POST",
        url="https://example.com/api",
        headers=headers or {"Content-Type": "application/json"},
        body=body,
        metadata={},
    )


def _resp(body: str = "", headers: dict | None = None) -> CapturedResponse:
    return CapturedResponse(
        status_code=200,
        headers=headers or {},
        body=body,
    )


def test_clean_request_passes():
    result = check_size_limits("req-1", _req(body="hello"))
    assert result.passed
    assert result.summary() == "req-1: OK"


def test_request_body_over_limit_flagged():
    large_body = "x" * 200
    result = check_size_limits("req-1", _req(body=large_body), max_request_body=100)
    assert not result.passed
    assert any(w.field == "body" and w.kind == "request" for w in result.warnings)


def test_request_body_at_limit_passes():
    body = "x" * 100
    result = check_size_limits("req-1", _req(body=body), max_request_body=100)
    assert result.passed


def test_response_body_over_limit_flagged():
    large_body = "y" * 500
    result = check_size_limits(
        "req-1", _req(), _resp(body=large_body), max_response_body=100
    )
    assert not result.passed
    assert any(w.field == "body" and w.kind == "response" for w in result.warnings)


def test_request_headers_over_limit_flagged():
    big_headers = {"X-Custom-" + str(i): "v" * 50 for i in range(10)}
    result = check_size_limits("req-1", _req(headers=big_headers), max_headers=100)
    assert not result.passed
    assert any(w.field == "headers" and w.kind == "request" for w in result.warnings)


def test_response_headers_over_limit_flagged():
    big_headers = {"X-H-" + str(i): "val" for i in range(30)}
    result = check_size_limits(
        "req-1", _req(), _resp(headers=big_headers), max_headers=50
    )
    assert not result.passed
    assert any(w.field == "headers" and w.kind == "response" for w in result.warnings)


def test_no_response_skips_response_checks():
    result = check_size_limits("req-1", _req(), resp=None, max_response_body=1)
    assert result.passed


def test_warning_to_dict_contains_keys():
    large_body = "x" * 200
    result = check_size_limits("req-1", _req(body=large_body), max_request_body=100)
    d = result.warnings[0].to_dict()
    assert "request_id" in d
    assert "kind" in d
    assert "field" in d
    assert "actual_bytes" in d
    assert "limit_bytes" in d


def test_summary_contains_sizes_on_failure():
    large_body = "z" * 200
    result = check_size_limits("req-1", _req(body=large_body), max_request_body=50)
    s = result.summary()
    assert "WARN" in s
    assert "B" in s


def test_scan_returns_result_per_pair():
    pairs = [(_req(), _resp()), (_req(body="x" * 500), None)]
    results = scan_size_limits(pairs, max_request_body=100)
    assert len(results) == 2
    assert results[0].passed
    assert not results[1].passed
