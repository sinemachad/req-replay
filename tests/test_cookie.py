"""Tests for req_replay.cookie."""
from __future__ import annotations

import pytest

from req_replay.cookie import extract_cookies, summarize_cookies, CookieSummary
from req_replay.models import CapturedRequest


def _req(cookie_header: str | None = None) -> CapturedRequest:
    headers = {"Content-Type": "application/json"}
    if cookie_header is not None:
        headers["Cookie"] = cookie_header
    return CapturedRequest(
        id="test-id",
        method="GET",
        url="https://example.com/api",
        headers=headers,
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
    )


def test_extract_cookies_empty_when_no_header():
    req = _req()
    assert extract_cookies(req) == {}


def test_extract_cookies_single():
    req = _req("session=abc123")
    result = extract_cookies(req)
    assert result == {"session": "abc123"}


def test_extract_cookies_multiple():
    req = _req("session=abc; token=xyz; lang=en")
    result = extract_cookies(req)
    assert result["session"] == "abc"
    assert result["token"] == "xyz"
    assert result["lang"] == "en"


def test_extract_cookies_case_insensitive_header_key():
    req = _req()
    req.headers["cookie"] = "user=bob"
    result = extract_cookies(req)
    assert result == {"user": "bob"}


def test_extract_cookies_invalid_header_returns_empty():
    req = _req()
    req.headers["Cookie"] = "!!!invalid!!!"
    # Should not raise; may return empty or partial
    result = extract_cookies(req)
    assert isinstance(result, dict)


def test_summarize_cookies_empty_list():
    summary = summarize_cookies([])
    assert summary.count == 0
    assert summary.names == []


def test_summarize_cookies_single_request():
    req = _req("session=abc; token=xyz")
    summary = summarize_cookies([req])
    assert summary.count == 2
    assert "session" in summary.names
    assert "token" in summary.names


def test_summarize_cookies_names_sorted():
    req = _req("z=1; a=2; m=3")
    summary = summarize_cookies([req])
    assert summary.names == sorted(summary.names)


def test_summarize_cookies_display_no_cookies():
    summary = CookieSummary()
    assert "No cookies" in summary.display()


def test_summarize_cookies_display_with_cookies():
    req = _req("session=abc")
    summary = summarize_cookies([req])
    output = summary.display()
    assert "session" in output
    assert "abc" in output
