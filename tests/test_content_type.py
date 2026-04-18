"""Tests for req_replay.content_type."""
from __future__ import annotations

from req_replay.content_type import analyze_content_types, _extract_content_type
from req_replay.models import CapturedRequest, CapturedResponse


def _req(ct: str | None = None) -> CapturedRequest:
    headers = {"Content-Type": ct} if ct else {}
    return CapturedRequest(
        id="req-1",
        method="POST",
        url="http://example.com/api",
        headers=headers,
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
    )


def _resp(ct: str | None = None) -> CapturedResponse:
    headers = {"Content-Type": ct} if ct else {}
    return CapturedResponse(status_code=200, headers=headers, body=None)


def test_extract_content_type_present():
    assert _extract_content_type({"content-type": "application/json"}) == "application/json"


def test_extract_content_type_strips_params():
    assert _extract_content_type({"Content-Type": "application/json; charset=utf-8"}) == "application/json"


def test_extract_content_type_missing():
    assert _extract_content_type({}) == "(none)"


def test_extract_content_type_case_insensitive():
    assert _extract_content_type({"CONTENT-TYPE": "text/plain"}) == "text/plain"


def test_empty_pairs_returns_empty_stats():
    stats = analyze_content_types([])
    assert stats.total_requests == 0
    assert stats.total_responses == 0


def test_single_pair_counted():
    pairs = [(_req("application/json"), _resp("application/json"))]
    stats = analyze_content_types(pairs)
    assert stats.request_types["application/json"] == 1
    assert stats.response_types["application/json"] == 1


def test_multiple_pairs_aggregated():
    pairs = [
        (_req("application/json"), _resp("application/json")),
        (_req("application/json"), _resp("text/html")),
        (_req("text/plain"), _resp("application/json")),
    ]
    stats = analyze_content_types(pairs)
    assert stats.request_types["application/json"] == 2
    assert stats.request_types["text/plain"] == 1
    assert stats.response_types["application/json"] == 2
    assert stats.response_types["text/html"] == 1


def test_no_content_type_header_counted_as_none():
    pairs = [(_req(), _resp())]
    stats = analyze_content_types(pairs)
    assert stats.request_types["(none)"] == 1
    assert stats.response_types["(none)"] == 1


def test_top_request_types_returns_most_common():
    pairs = [
        (_req("application/json"), _resp()),
        (_req("application/json"), _resp()),
        (_req("text/plain"), _resp()),
    ]
    stats = analyze_content_types(pairs)
    top = stats.top_request_types(1)
    assert top[0][0] == "application/json"
    assert top[0][1] == 2


def test_display_contains_headers():
    pairs = [(_req("application/json"), _resp("text/html"))]
    stats = analyze_content_types(pairs)
    output = stats.display()
    assert "Request Content-Types" in output
    assert "Response Content-Types" in output
    assert "application/json" in output
    assert "text/html" in output
