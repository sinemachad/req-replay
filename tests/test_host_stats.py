"""Tests for req_replay.host_stats."""
import pytest
from req_replay.host_stats import analyze_hosts, _extract_host
from req_replay.models import CapturedRequest


def _req(url: str) -> CapturedRequest:
    return CapturedRequest(
        id="test",
        method="GET",
        url=url,
        headers={},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


def test_empty_list_returns_zero_stats():
    stats = analyze_hosts([])
    assert stats.total == 0
    assert stats.host_counts == {}
    assert stats.top_hosts == []


def test_single_request_counted():
    stats = analyze_hosts([_req("https://example.com/path")])
    assert stats.total == 1
    assert stats.host_counts.get("example.com") == 1


def test_multiple_requests_same_host():
    reqs = [_req("https://api.example.com/a") for _ in range(5)]
    stats = analyze_hosts(reqs)
    assert stats.host_counts["api.example.com"] == 5


def test_multiple_hosts_counted_separately():
    reqs = [
        _req("https://alpha.io/x"),
        _req("https://beta.io/y"),
        _req("https://alpha.io/z"),
    ]
    stats = analyze_hosts(reqs)
    assert stats.host_counts["alpha.io"] == 2
    assert stats.host_counts["beta.io"] == 1


def test_top_hosts_sorted_by_frequency():
    reqs = (
        [_req("https://a.com/")] * 3
        + [_req("https://b.com/")] * 5
        + [_req("https://c.com/")] * 1
    )
    stats = analyze_hosts(reqs)
    assert stats.top_hosts[0] == ("b.com", 5)
    assert stats.top_hosts[1] == ("a.com", 3)


def test_top_n_limits_results():
    reqs = [_req(f"https://host{i}.com/") for i in range(20)]
    stats = analyze_hosts(reqs, top_n=5)
    assert len(stats.top_hosts) == 5


def test_extract_host_standard_url():
    assert _extract_host("https://example.com/foo") == "example.com"


def test_extract_host_with_port():
    assert _extract_host("http://localhost:8080/bar") == "localhost:8080"


def test_display_empty():
    stats = analyze_hosts([])
    assert "No requests" in stats.display()


def test_display_contains_host():
    stats = analyze_hosts([_req("https://myapi.io/v1")])
    assert "myapi.io" in stats.display()
