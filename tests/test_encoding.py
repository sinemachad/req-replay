"""Tests for req_replay.encoding."""
import pytest
from req_replay.encoding import analyze_encodings, EncodingStats
from req_replay.models import CapturedRequest, CapturedResponse
from datetime import datetime


def _req(headers=None) -> CapturedRequest:
    return CapturedRequest(
        id="req-1",
        method="POST",
        url="https://example.com/api",
        headers=headers or {},
        body=None,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        tags=[],
        metadata={},
    )


def _resp(headers=None, status=200) -> CapturedResponse:
    return CapturedResponse(
        status_code=status,
        headers=headers or {},
        body=None,
        elapsed_ms=50.0,
    )


def test_empty_lists_return_zero_stats():
    stats = analyze_encodings([], [])
    assert stats.total_requests == 0
    assert stats.total_responses == 0
    assert stats.request_encodings == {}
    assert stats.response_encodings == {}


def test_request_gzip_encoding_counted():
    req = _req(headers={"Content-Encoding": "gzip"})
    stats = analyze_encodings([req], [None])
    assert stats.request_encodings.get("gzip") == 1


def test_response_br_encoding_counted():
    resp = _resp(headers={"content-encoding": "br"})
    stats = analyze_encodings([_req()], [resp])
    assert stats.response_encodings.get("br") == 1


def test_multiple_requests_counted():
    reqs = [
        _req(headers={"Content-Encoding": "gzip"}),
        _req(headers={"Content-Encoding": "gzip"}),
        _req(headers={"Content-Encoding": "deflate"}),
    ]
    stats = analyze_encodings(reqs, [None, None, None])
    assert stats.request_encodings["gzip"] == 2
    assert stats.request_encodings["deflate"] == 1


def test_transfer_encoding_fallback():
    req = _req(headers={"Transfer-Encoding": "chunked"})
    stats = analyze_encodings([req], [None])
    assert stats.request_encodings.get("chunked") == 1


def test_unknown_encoding_recorded():
    req = _req(headers={"Content-Encoding": "zstd"})
    stats = analyze_encodings([req], [None])
    assert "zstd" in stats.unknown_encodings


def test_no_encoding_header_not_counted():
    req = _req(headers={"Content-Type": "application/json"})
    stats = analyze_encodings([req], [None])
    assert stats.request_encodings == {}


def test_display_contains_labels():
    req = _req(headers={"Content-Encoding": "gzip"})
    resp = _resp(headers={"content-encoding": "br"})
    stats = analyze_encodings([req], [resp])
    out = stats.display()
    assert "gzip" in out
    assert "br" in out
    assert "Requests analysed" in out


def test_none_responses_excluded_from_total():
    stats = analyze_encodings([_req(), _req()], [None, None])
    assert stats.total_responses == 0
