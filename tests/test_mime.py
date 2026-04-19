"""Tests for req_replay.mime."""
from collections import Counter
from req_replay.mime import analyze_mime, _extract_mime, MimeStats
from req_replay.models import CapturedRequest, CapturedResponse
import pytest


def _req(content_type: str = "application/json", body: str = "{}") -> CapturedRequest:
    return CapturedRequest(
        id="r1",
        method="POST",
        url="http://example.com/api",
        headers={"Content-Type": content_type},
        body=body,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


def _resp(content_type: str = "application/json", body: str = "{}") -> CapturedResponse:
    return CapturedResponse(
        status_code=200,
        headers={"Content-Type": content_type},
        body=body,
    )


def test_extract_mime_present():
    headers = {"Content-Type": "application/json; charset=utf-8"}
    assert _extract_mime(headers) == "application/json"


def test_extract_mime_missing():
    assert _extract_mime({}) == "unknown"


def test_extract_mime_case_insensitive():
    headers = {"content-type": "text/html"}
    assert _extract_mime(headers) == "text/html"


def test_empty_pairs_returns_zero_stats():
    stats = analyze_mime([])
    assert stats.total_requests == 0
    assert stats.total_responses == 0


def test_single_json_pair_counted():
    stats = analyze_mime([(_req(), _resp())])
    assert stats.total_requests == 1
    assert stats.total_responses == 1
    assert stats.request_types["application/json"] == 1
    assert stats.response_types["application/json"] == 1


def test_no_body_not_counted():
    req = _req(body=None)
    resp = _resp(body=None)
    stats = analyze_mime([(req, resp)])
    assert stats.total_requests == 0
    assert stats.total_responses == 0


def test_top_request_types_limited():
    pairs = [
        (_req("application/json"), _resp()),
        (_req("text/plain"), _resp()),
        (_req("application/xml"), _resp()),
    ]
    stats = analyze_mime(pairs)
    top = stats.top_request_types(2)
    assert len(top) == 2


def test_display_contains_labels():
    stats = analyze_mime([(_req(), _resp())])
    out = stats.display()
    assert "MIME Type Analysis" in out
    assert "application/json" in out


def test_multiple_same_type_counted():
    pairs = [(_req("text/xml"), _resp("text/xml")) for _ in range(3)]
    stats = analyze_mime(pairs)
    assert stats.request_types["text/xml"] == 3
    assert stats.response_types["text/xml"] == 3
