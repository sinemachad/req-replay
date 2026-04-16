"""Tests for req_replay.filter module."""
import pytest
from datetime import datetime, timezone

from req_replay.models import CapturedRequest
from req_replay.filter import FilterCriteria, filter_requests


def _req(
    method: str = "GET",
    url: str = "https://example.com/api/v1/users",
    tags: list | None = None,
) -> CapturedRequest:
    return CapturedRequest(
        id="abc123",
        method=method,
        url=url,
        headers={"Content-Type": "application/json"},
        body=None,
        timestamp=datetime.now(timezone.utc).isoformat(),
        tags=tags or [],
    )


SAMPLE = [
    _req("GET",  "https://example.com/api/v1/users",   ["smoke"]),
    _req("POST", "https://example.com/api/v1/users",   ["smoke", "auth"]),
    _req("GET",  "https://other.io/health",            []),
    _req("DELETE", "https://example.com/api/v1/users/42", ["auth"]),
]


def test_no_criteria_returns_all():
    result = filter_requests(SAMPLE, FilterCriteria())
    assert result == SAMPLE


def test_filter_by_method():
    result = filter_requests(SAMPLE, FilterCriteria(method="GET"))
    assert all(r.method == "GET" for r in result)
    assert len(result) == 2


def test_filter_by_method_case_insensitive():
    result = filter_requests(SAMPLE, FilterCriteria(method="post"))
    assert len(result) == 1
    assert result[0].method == "POST"


def test_filter_by_url_pattern():
    result = filter_requests(SAMPLE, FilterCriteria(url_pattern=r"/users/\d+"))
    assert len(result) == 1
    assert "42" in result[0].url


def test_filter_by_host():
    result = filter_requests(SAMPLE, FilterCriteria(host="other.io"))
    assert len(result) == 1
    assert result[0].url == "https://other.io/health"


def test_filter_by_single_tag():
    result = filter_requests(SAMPLE, FilterCriteria(tags=["auth"]))
    assert len(result) == 2


def test_filter_by_multiple_tags():
    result = filter_requests(SAMPLE, FilterCriteria(tags=["smoke", "auth"]))
    assert len(result) == 1
    assert result[0].method == "POST"


def test_filter_combined_method_and_tag():
    result = filter_requests(SAMPLE, FilterCriteria(method="GET", tags=["smoke"]))
    assert len(result) == 1
    assert result[0].url == "https://example.com/api/v1/users"


def test_invalid_regex_raises_value_error():
    with pytest.raises(ValueError, match="Invalid url_pattern regex"):
        filter_requests(SAMPLE, FilterCriteria(url_pattern="[invalid"))


def test_empty_list_returns_empty():
    result = filter_requests([], FilterCriteria(method="GET"))
    assert result == []


def test_filter_by_tag_no_match_returns_empty():
    """A tag that no request carries should yield an empty result."""
    result = filter_requests(SAMPLE, FilterCriteria(tags=["nonexistent"]))
    assert result == []


def test_filter_by_host_no_match_returns_empty():
    """A host that no request targets should yield an empty result."""
    result = filter_requests(SAMPLE, FilterCriteria(host="unknown.example.com"))
    assert result == []
