"""Tests for req_replay.compare."""
import pytest
from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.compare import compare_requests, CompareResult


def _req(
    id_="a",
    method="GET",
    url="https://example.com/api",
    headers=None,
    body=None,
):
    return CapturedRequest(
        id=id_,
        method=method,
        url=url,
        headers=headers or {"Content-Type": "application/json"},
        body=body,
        timestamp="2024-01-01T00:00:00",
        tags=[],
    )


def _resp(status=200, headers=None, body=b"ok"):
    return CapturedResponse(
        status_code=status,
        headers=headers or {"Content-Type": "text/plain"},
        body=body,
        elapsed_ms=50.0,
    )


def test_identical_requests_are_equivalent():
    a = _req(id_="a")
    b = _req(id_="b")
    result = compare_requests(a, b)
    assert result.requests_equivalent is True


def test_url_mismatch_detected():
    a = _req(id_="a", url="https://example.com/foo")
    b = _req(id_="b", url="https://example.com/bar")
    result = compare_requests(a, b)
    assert result.url_match is False
    assert result.requests_equivalent is False


def test_method_mismatch_detected():
    a = _req(id_="a", method="GET")
    b = _req(id_="b", method="POST")
    result = compare_requests(a, b)
    assert result.method_match is False


def test_method_comparison_is_case_insensitive():
    a = _req(id_="a", method="get")
    b = _req(id_="b", method="GET")
    result = compare_requests(a, b)
    assert result.method_match is True


def test_extra_header_in_a_detected():
    a = _req(id_="a", headers={"X-Extra": "yes", "Content-Type": "application/json"})
    b = _req(id_="b", headers={"Content-Type": "application/json"})
    result = compare_requests(a, b)
    assert "X-Extra" in result.headers_only_in_a
    assert result.requests_equivalent is False


def test_extra_header_in_b_detected():
    a = _req(id_="a", headers={"Content-Type": "application/json"})
    b = _req(id_="b", headers={"Content-Type": "application/json", "X-Token": "abc"})
    result = compare_requests(a, b)
    assert "X-Token" in result.headers_only_in_b


def test_body_mismatch_detected():
    a = _req(id_="a", body=b"hello")
    b = _req(id_="b", body=b"world")
    result = compare_requests(a, b)
    assert result.body_match is False


def test_response_diff_included_when_provided():
    a = _req(id_="a")
    b = _req(id_="b")
    ra = _resp(status=200, body=b"ok")
    rb = _resp(status=404, body=b"not found")
    result = compare_requests(a, b, ra, rb)
    assert result.response_diff is not None
    assert not result.response_diff.is_identical


def test_response_diff_none_when_not_provided():
    a = _req(id_="a")
    b = _req(id_="b")
    result = compare_requests(a, b)
    assert result.response_diff is None


def test_summary_contains_ids():
    a = _req(id_="req-001")
    b = _req(id_="req-002")
    result = compare_requests(a, b)
    summary = result.summary()
    assert "req-001" in summary
    assert "req-002" in summary
